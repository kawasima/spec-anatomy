import { defineConfig } from "vite";
import { resolve, join, normalize, relative, dirname } from "path";
import { existsSync, statSync, readFileSync, writeFileSync, mkdirSync } from "fs";

const REPO_ROOT = resolve(".");

// docs/、tools/、ルートの md などを生ファイルとして配信するミドルウェア。
// Vite の root は viewer/ なので、それ以外のリポジトリ内パスは
// 自前で読み込んで返す。
function repoFilesPlugin() {
  const ALLOW_PREFIXES = ["/docs/", "/reference/", "/tools/", "/sdd.md", "/sdd-vs-traditional-design-docs.md", "/README.md"];
  const MIME = {
    md: "text/markdown; charset=utf-8",
    html: "text/html; charset=utf-8",
    htm: "text/html; charset=utf-8",
    css: "text/css; charset=utf-8",
    js: "text/javascript; charset=utf-8",
    mjs: "text/javascript; charset=utf-8",
    json: "application/json; charset=utf-8",
    png: "image/png",
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    gif: "image/gif",
    svg: "image/svg+xml",
    txt: "text/plain; charset=utf-8",
  };

  // 書き込み許可するパス（プロジェクト仕様の書き場所のみ）
  const WRITABLE_PREFIXES = ["docs/"];
  const WRITABLE_EXTS = new Set(["md", "html", "png"]);

  function isPathSafe(rel) {
    // .. を含む / 絶対パス / 許可ディレクトリ外を弾く
    if (!rel || rel.startsWith("/") || rel.includes("\\")) return false;
    const normalized = normalize(rel);
    if (normalized.startsWith("..") || normalized.startsWith("/")) return false;
    if (!WRITABLE_PREFIXES.some((p) => normalized.startsWith(p))) return false;
    const ext = normalized.split(".").pop().toLowerCase();
    if (!WRITABLE_EXTS.has(ext)) return false;
    return true;
  }

  function readJsonBody(req) {
    return new Promise((resolve, reject) => {
      let buf = "";
      req.setEncoding("utf8");
      req.on("data", (c) => (buf += c));
      req.on("end", () => {
        try {
          resolve(JSON.parse(buf));
        } catch (e) {
          reject(e);
        }
      });
      req.on("error", reject);
    });
  }

  function writeFileSafe(rel, content, mode = "utf8") {
    const filepath = join(REPO_ROOT, rel);
    mkdirSync(dirname(filepath), { recursive: true });
    if (mode === "base64") {
      writeFileSync(filepath, Buffer.from(content, "base64"));
    } else {
      writeFileSync(filepath, content, "utf8");
    }
  }

  return {
    name: "repo-files",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = (req.url || "").split("?")[0];

        // POST /api/save-screen — screen.md と PNG を1リクエストで保存
        if (req.method === "POST" && url === "/api/save-screen") {
          try {
            const body = await readJsonBody(req);
            const written = [];
            // body = { md: { path, content }, png?: { path, base64 } }
            if (body.md?.path && body.md?.content != null) {
              if (!isPathSafe(body.md.path)) {
                res.statusCode = 403;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "forbidden md path" }));
                return;
              }
              writeFileSafe(body.md.path, body.md.content, "utf8");
              written.push(body.md.path);
            }
            if (body.png?.path && body.png?.base64) {
              if (!isPathSafe(body.png.path)) {
                res.statusCode = 403;
                res.setHeader("Content-Type", "application/json");
                res.end(JSON.stringify({ error: "forbidden png path" }));
                return;
              }
              writeFileSafe(body.png.path, body.png.base64, "base64");
              written.push(body.png.path);
            }
            res.statusCode = 200;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ written }));
          } catch (e) {
            res.statusCode = 400;
            res.setHeader("Content-Type", "application/json");
            res.end(JSON.stringify({ error: e.message }));
          }
          return;
        }

        // GET 系: 既存のファイル配信
        const allowed = ALLOW_PREFIXES.some((p) => url === p || url.startsWith(p));
        if (!allowed) return next();

        const filepath = join(REPO_ROOT, url);
        if (!existsSync(filepath) || !statSync(filepath).isFile()) {
          return next();
        }
        const ext = filepath.split(".").pop().toLowerCase();
        res.setHeader("Content-Type", MIME[ext] || "application/octet-stream");
        res.end(readFileSync(filepath));
      });
    },
  };
}

// 1つの Vite サーバで viewer (/) と oppsett (/oppsett/) を配信する。
export default defineConfig({
  root: "viewer",
  publicDir: false,
  plugins: [repoFilesPlugin()],
  server: {
    port: 5173,
    fs: {
      allow: [".."],
    },
  },
  build: {
    outDir: "../dist",
    emptyOutDir: true,
  },
});
