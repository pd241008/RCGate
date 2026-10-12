/// <reference types="vite/client" />

declare module "*.md?url" {
  const url: string;
  export default url;
}

declare module "*.css?raw" {
  const css: string;
  export default css;
}
