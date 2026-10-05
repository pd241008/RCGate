"""RC-Gate: reliability-conditioned gated mixture-of-experts (spec section 6).

    x_meta = [Emb_type(claim_type) || Emb_gen(generator_id)]      # 4-d + 4-d
    gate   = MLP(8 -> 16 -> 2)                                    # ReLU
    w      = softmax(gate(x_meta) / tau)                          # tau from config
    z_c    = Linear(3 -> 1)(s_cross)
    z_e    = Linear(3 -> 1)(s_evid)
    logit  = Phi([w_c * z_c, w_e * z_e])
    P      = sigmoid(logit)

Trained end to end with BCE on P. Experts and meta-learner are *not* fit in separate
stages; A3 is the staged/flat-blend control instead.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn

from ..data.schema import CROSS_SIGNALS, EVID_SIGNALS, UNK_GENERATOR
from ..metrics import auroc
from ..utils import count_parameters, device
from .baselines import SignalModel
from .experts import CrossModelExpert, EvidenceExpert
from .gate import Gate, MetadataEncoder
from .meta import FusionHead, Prediction

#: Config key -> GATE_VARIANTS entry name, for the "gate sees signals too" ablation.
SEES_SIGNALS_VARIANT = "A7_sees_signals"


@dataclass
class RCGateConfig:
    n_generators: int = 3
    use_claim_type: bool = True
    use_generator: bool = True
    claim_type_emb_dim: int = 4
    generator_emb_dim: int = 4
    gate_hidden: int = 16
    gate_temp: float = 1.0
    fusion_input: str = "logit"  # "logit" | "prob"
    unk_dropout: float = 0.1
    dropout: float = 0.0
    see_signals_in_gate: bool = False
    fusion_bias: bool = True
    standardize_signals: bool = False
    # training
    epochs: int = 60
    batch_size: int = 128
    lr: float = 3e-3
    weight_decay: float = 1e-4
    patience: int = 8
    grad_clip: float = 1.0

    @classmethod
    def from_config(cls, cfg, variant: str = "A7") -> RCGateConfig:
        model = cfg.get("model", {})
        train = cfg.get("train", {})
        sees = variant == SEES_SIGNALS_VARIANT or bool(model.get("see_signals_in_gate", False))
        return cls(
            n_generators=int(model.get("n_generators", 3)),
            use_claim_type=variant != "A6",
            use_generator=variant != "A5",
            claim_type_emb_dim=int(model.get("claim_type_emb_dim", 4)),
            generator_emb_dim=int(model.get("generator_emb_dim", 4)),
            gate_hidden=int(model.get("gate_hidden", 16)),
            gate_temp=float(model.get("gate_temp", 1.0)),
            fusion_input=str(model.get("fusion_input", "logit")),
            unk_dropout=float(model.get("unk_dropout", 0.1)),
            dropout=float(model.get("dropout", 0.0)),
            see_signals_in_gate=sees,
            fusion_bias=bool(model.get("fusion_bias", True)),
            standardize_signals=bool(model.get("standardize_signals", False)),
            epochs=int(train.get("epochs", 60)),
            batch_size=int(train.get("batch_size", 128)),
            lr=float(train.get("lr", 3e-3)),
            weight_decay=float(train.get("weight_decay", 1e-4)),
            patience=int(train.get("patience", 8)),
            grad_clip=float(train.get("grad_clip", 1.0)),
        )


class RCGate(nn.Module):
    """The full gated mixture-of-experts. About 230 parameters, well under the 50k cap."""

    def __init__(self, config: RCGateConfig) -> None:
        super().__init__()
        self.config = config
        n_all_signals = len(CROSS_SIGNALS) + len(EVID_SIGNALS)

        self.encoder = MetadataEncoder(
            n_generators=config.n_generators,
            type_dim=config.claim_type_emb_dim if config.use_claim_type else 0,
            generator_dim=config.generator_emb_dim if config.use_generator else 0,
            see_signals=config.see_signals_in_gate,
            n_signals=n_all_signals,
        )
        self.gate = Gate(
            in_dim=self.encoder.output_dim,
            hidden=config.gate_hidden,
            tau=config.gate_temp,
            dropout=config.dropout,
        )
        self.cross_expert = CrossModelExpert()
        self.evid_expert = EvidenceExpert()
        self.fusion = FusionHead(2, bias=config.fusion_bias)

        # Optional standardisation buffers. Off by default: all six signals are already in
        # [0, 1], so the spec's unscaled Linear(3 -> 1) is a fair reading and avoids an
        # unrequested transformation of the inputs.
        n = n_all_signals
        self.register_buffer("signal_mean", torch.zeros(n))
        self.register_buffer("signal_std", torch.ones(n))

    # -- input preparation ------------------------------------------------
    def set_signal_stats(self, stats: tuple[np.ndarray, np.ndarray]) -> None:
        mean, std = stats
        self.signal_mean = torch.as_tensor(mean, dtype=torch.float32)
        self.signal_std = torch.as_tensor(std, dtype=torch.float32).clamp_min(1e-6)

    def scale_signals(self, s: torch.Tensor) -> torch.Tensor:
        if not self.config.standardize_signals:
            return s
        return (s - self.signal_mean) / self.signal_std

    # -- forward ----------------------------------------------------------
    def forward(
        self,
        claim_type: torch.Tensor,
        generator_id: torch.Tensor,
        s_cross: torch.Tensor,
        s_evid: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        # The gate is fed metadata only (constraint: the gate must not see the signals).
        x_meta = self.encoder(claim_type, generator_id)
        w = self.gate(x_meta)

        z_cross = self.cross_expert(self.scale_signals(s_cross))
        z_evid = self.evid_expert(self.scale_signals(s_evid))

        if self.config.fusion_input == "prob":
            fused_cross = w[:, 0] * torch.sigmoid(z_cross)
            fused_evid = w[:, 1] * torch.sigmoid(z_evid)
        else:
            fused_cross = w[:, 0] * z_cross
            fused_evid = w[:, 1] * z_evid

        logit = self.fusion(torch.stack([fused_cross, fused_evid], dim=-1))
        return {
            "w": w,
            "z_cross": z_cross,
            "z_evid": z_evid,
            "fused": torch.stack([fused_cross, fused_evid], dim=-1),
            "logit": logit,
            "prob": torch.sigmoid(logit),
        }

    # -- introspection ----------------------------------------------------
    def explain(self, **batch) -> dict[str, np.ndarray]:
        """Gate weights and expert logits, unbatched and detached."""
        out = self.forward(**batch)
        return {
            "w_cross": out["w"][:, 0].detach().numpy(),
            "w_evid": out["w"][:, 1].detach().numpy(),
            "z_cross": out["z_cross"].detach().numpy(),
            "z_evid": out["z_evid"].detach().numpy(),
            "logit": out["logit"].detach().numpy(),
            "prob": out["prob"].detach().numpy(),
        }

    @property
    def n_parameters(self) -> int:
        return count_parameters(self)


def frame_to_batch(df: pd.DataFrame, n_generators: int) -> dict[str, torch.Tensor]:
    """Turn signal-table rows into tensors, mapping ``UNK`` onto the extra embedding row."""
    gen = df["generator_id"].to_numpy()
    gen = np.where(gen == UNK_GENERATOR, n_generators, gen).astype("int64")
    return {
        "claim_type": torch.as_tensor(df["claim_type"].to_numpy(), dtype=torch.long),
        "generator_id": torch.as_tensor(gen, dtype=torch.long),
        "s_cross": torch.as_tensor(
            df[CROSS_SIGNALS].to_numpy(dtype="float32"), dtype=torch.float32
        ),
        "s_evid": torch.as_tensor(df[EVID_SIGNALS].to_numpy(dtype="float32"), dtype=torch.float32),
    }


def _labels(df: pd.DataFrame) -> torch.Tensor:
    return torch.as_tensor(df["label"].to_numpy(), dtype=torch.float32)


class RCGateModel(SignalModel):
    """Trainable variant wrapper matching the :class:`SignalModel` interface."""

    def __init__(self, config: RCGateConfig, seed: int = 0, name: str = "A7") -> None:
        self.config = config
        self.seed = seed
        self.name = name
        self.model = RCGate(config)
        self.dev = device()
        self.model.to(self.dev)
        self._last_frame: pd.DataFrame | None = None
        self.fit_info: dict[str, Any] = {}

    # -- training ---------------------------------------------------------
    def fit(self, train: pd.DataFrame, val: pd.DataFrame, cfg=None) -> dict:
        torch.manual_seed(self.seed)
        c = self.config

        if c.standardize_signals:
            all_signals = train[CROSS_SIGNALS + EVID_SIGNALS].to_numpy(dtype="float64")
            self.model.set_signal_stats((all_signals.mean(axis=0), all_signals.std(axis=0)))

        x_train, y_train = frame_to_batch(train, c.n_generators), _labels(train)
        x_val, y_val = frame_to_batch(val, c.n_generators), _labels(val)
        n = len(train)

        optimiser = torch.optim.Adam(
            self.model.parameters(), lr=c.lr, weight_decay=c.weight_decay
        )
        loss_fn = nn.BCEWithLogitsLoss()

        gen_rng = np.random.default_rng(self.seed)
        batch_size = max(1, min(c.batch_size, n))
        best_auc, best_state, best_epoch, bad_epochs = -np.inf, None, -1, 0
        history: list[dict[str, float]] = []

        for epoch in range(c.epochs):
            self.model.train()
            order = gen_rng.permutation(n)
            total_loss, batches = 0.0, 0
            for start in range(0, n, batch_size):
                idx = torch.as_tensor(order[start : start + batch_size], dtype=torch.long)
                batch = {k: v[idx] for k, v in x_train.items()}
                labels = y_train[idx]

                # Cold-start training: send the generator to UNK sometimes so that path is
                # learned rather than hoped for (proposal, open challenge 5).
                if c.unk_dropout > 0 and c.use_generator:
                    flip = torch.as_tensor(
                        gen_rng.random(idx.shape[0]) < c.unk_dropout, dtype=torch.bool
                    )
                    unk = torch.full_like(batch["generator_id"], c.n_generators)
                    batch["generator_id"] = torch.where(flip, unk, batch["generator_id"])

                optimiser.zero_grad()
                out = self.model(**batch)
                loss = loss_fn(out["logit"], labels)
                loss.backward()
                if c.grad_clip > 0:
                    nn.utils.clip_grad_norm_(self.model.parameters(), c.grad_clip)
                optimiser.step()
                total_loss += float(loss.detach())
                batches += 1

            val_auc = self._val_auroc(x_val, y_val)
            history.append({"epoch": epoch, "train_loss": total_loss / max(batches, 1), "val_auroc": val_auc})
            if val_auc > best_auc + 1e-6:
                best_auc, best_epoch, bad_epochs = val_auc, epoch, 0
                best_state = copy.deepcopy(self.model.state_dict())
            else:
                bad_epochs += 1
                if bad_epochs >= c.patience:
                    break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        self.fit_info = {
            "val_auroc": best_auc,
            "best_epoch": best_epoch,
            "epochs_run": len(history),
            "n_parameters": self.model.n_parameters,
            "gate_input_dim": self.model.encoder.output_dim,
            "fusion_input": c.fusion_input,
            "unk_dropout": c.unk_dropout,
        }
        return self.fit_info

    @torch.no_grad()
    def _val_auroc(self, x_val: dict[str, torch.Tensor], y_val: torch.Tensor) -> float:
        self.model.eval()
        prob = self.model(**x_val)["prob"].numpy()
        return auroc(y_val.numpy(), prob)

    # -- inference --------------------------------------------------------
    @torch.no_grad()
    def predict_frame(self, df: pd.DataFrame) -> dict[str, np.ndarray]:
        self.model.eval()
        return self.model.explain(**frame_to_batch(df, self.config.n_generators))

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        out = self.predict_frame(df)
        self._last_frame = df.reset_index(drop=True)
        return out["prob"].astype("float64")

    def predict(self, df: pd.DataFrame) -> list[Prediction]:
        """Return one :class:`Prediction` per row. Never a bare probability array."""
        out = self.predict_frame(df)
        return [
            Prediction(
                prob=float(p),
                w_cross=float(wc),
                w_evid=float(we),
                z_cross=float(zc),
                z_evid=float(ze),
            )
            for p, wc, we, zc, ze in zip(
                out["prob"], out["w_cross"], out["w_evid"], out["z_cross"], out["z_evid"],
                strict=True,
            )
        ]

    def gate_weight_frame(self) -> pd.DataFrame | None:
        """Gate weights for the most recently predicted frame, keyed for aggregation."""
        if self._last_frame is None:
            return None
        out = self.predict_frame(self._last_frame)
        return pd.DataFrame(
            {
                "claim_type": self._last_frame["claim_type"].to_numpy(),
                "generator_id": self._last_frame["generator_id"].to_numpy(),
                "w_cross": out["w_cross"],
                "w_evid": out["w_evid"],
                "z_cross": out["z_cross"],
                "z_evid": out["z_evid"],
            }
        )

    def info(self) -> dict:
        return dict(self.fit_info)


def build_gate_variant(variant: str, cfg, seed: int = 0) -> RCGateModel:
    """Factory for A5, A6, A7 and the labelled "gate sees signals" ablation."""
    return RCGateModel(RCGateConfig.from_config(cfg, variant=variant), seed=seed, name=variant)
