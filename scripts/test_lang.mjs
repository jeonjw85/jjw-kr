import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(join(ROOT, "index.html"), "utf8");

const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
if (!scriptMatch) {
  console.error("FAIL: index.html에 인라인 스크립트가 없다");
  process.exit(1);
}
const script = scriptMatch[1];

const els = [];
const re =
  /<(\w+)([^>]*\bdata-ko="([^"]*)"[^>]*\bdata-en="([^"]*)"[^>]*)>([^<]*)</g;
let m;
while ((m = re.exec(html)) !== null) {
  const attrs = m[2];
  const idMatch = attrs.match(/\bid="([^"]*)"/);
  els.push({
    tag: m[1],
    id: idMatch ? idMatch[1] : null,
    attrs: { "data-ko": m[3], "data-en": m[4] },
    textContent: m[5],
    innerHTML: "",
    getAttribute(name) {
      return this.attrs[name] ?? null;
    },
    setAttribute(name, value) {
      this.attrs[name] = value;
    },
  });
}

const langBtn = {
  id: "lang",
  attrs: {
    "aria-pressed": "false",
    "aria-label": "KO / EN — Switch to English",
  },
  innerHTML: "",
  listeners: {},
  getAttribute(n) {
    return this.attrs[n] ?? null;
  },
  setAttribute(n, v) {
    this.attrs[n] = v;
  },
  addEventListener(type, fn) {
    this.listeners[type] = fn;
  },
};

const header = {
  classes: new Set(),
  classList: {
    toggle(name, on) {
      if (on) header.classes.add(name);
      else header.classes.delete(name);
    },
  },
};

const store = new Map();
const root = { lang: "ko" };
let scrollY = 0;

const document = {
  documentElement: root,
  getElementById: (id) => (id === "lang" ? langBtn : null),
  querySelectorAll: (sel) =>
    sel === "[data-ko][data-en]" ? els : [],
  querySelector: (sel) => (sel === ".site-header" ? header : null),
};
const navigator = { language: "ko-KR" };
const localStorage = {
  getItem: (k) => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, v),
};
const window = {
  scrollY: 0,
  addEventListener(type, fn) {
    if (type === "scroll") window._scroll = fn;
  },
};

new Function(
  "document",
  "navigator",
  "localStorage",
  "window",
  script,
)(document, navigator, localStorage, window);

let failed = 0;
function check(name, cond, detail = "") {
  if (cond) {
    console.log(`PASS ${name}`);
  } else {
    failed++;
    console.log(`FAIL ${name}${detail ? `: ${detail}` : ""}`);
  }
}

const enEls = els.filter((e) => e.textContent === e.attrs["data-en"]);
check(
  "초기 상태가 영어다 (JS 없이도 읽히는 기본값과 동일)",
  enEls.length === els.length,
  `${enEls.length}/${els.length}`,
);
check("초기 html lang이 en", root.lang === "en");
check(
  "초기 버튼 라벨이 한국어로 전환을 포함",
  langBtn.getAttribute("aria-label").includes("한국어로 전환"),
);
check(
  "en 상태: 접근성 이름에 보이는 텍스트 KO / EN 포함",
  langBtn.getAttribute("aria-label").includes("KO / EN"),
  langBtn.getAttribute("aria-label"),
);
check("초기 버튼 텍스트가 EN", langBtn.textContent === "EN", langBtn.textContent);

langBtn.listeners.click();

check(
  "클릭 후 모든 요소가 한국어로 바뀐다",
  els.every((e) => e.textContent === e.attrs["data-ko"]),
);
check("클릭 후 html lang이 ko", root.lang === "ko");
check("클릭 후 aria-pressed=true (KO 표시 중)", langBtn.getAttribute("aria-pressed") === "true");
check(
    "클릭 후 버튼 라벨이 Switch to English를 포함",
    langBtn.getAttribute("aria-label").includes("Switch to English"),
);
check("클릭 후 버튼 텍스트가 KO", langBtn.textContent === "KO", langBtn.textContent);

langBtn.listeners.click();

check(
  "두 번째 클릭으로 영어 복귀",
  els.every((e) => e.textContent === e.attrs["data-en"]),
);
check("두 번째 클릭 후 html lang이 en", root.lang === "en");
check("저장값을 남기지 않는다", store.size === 0, String(store.size));

if (failed) {
  console.log(`\n${failed} failed`);
  process.exit(1);
}

const staticBtn = html.match(/<button[^>]*id="lang"[^>]*>/)[0];
const staticLabel = staticBtn.match(/aria-label="([^"]*)"/)[1];
let staticFail = 0;
if (!staticLabel.includes("KO / EN")) {
  staticFail++;
  console.log(`FAIL 정적 HTML aria-label에 보이는 텍스트 없음: ${staticLabel}`);
} else {
  console.log("PASS 정적 HTML aria-label이 보이는 텍스트를 포함");
}
if (staticFail) process.exit(1);

console.log(`\n${els.length}개 이중언어 요소, 토글 왕복 검증 통과`);

function freshRun({ storedLang, browserLanguage }) {
  const store2 = new Map();
  if (storedLang) store2.set("lang", storedLang);
  const root2 = { lang: "ko" };
  const els2 = els.map((e) => ({
    ...e,
    attrs: { ...e.attrs },
    textContent: e.attrs["data-ko"],
  }));
  const btn2 = {
    attrs: {},
    innerHTML: "",
    listeners: {},
    getAttribute(n) {
      return this.attrs[n] ?? null;
    },
    setAttribute(n, v) {
      this.attrs[n] = v;
    },
    addEventListener(t, f) {
      this.listeners[t] = f;
    },
  };
  const header2 = {
    classes: new Set(),
    classList: {
      toggle(n, on) {
        if (on) header2.classes.add(n);
        else header2.classes.delete(n);
      },
    },
  };
  const doc2 = {
    documentElement: root2,
    getElementById: () => btn2,
    querySelectorAll: () => els2,
    querySelector: () => header2,
  };
  const nav2 = { language: browserLanguage };
  const ls2 = {
    getItem: (k) => (store2.has(k) ? store2.get(k) : null),
    setItem: (k, v) => store2.set(k, v),
  };
  const win2 = {
    scrollY: 100,
    addEventListener() {},
  };
  new Function("document", "navigator", "localStorage", "window", script)(
    doc2,
    nav2,
    ls2,
    win2,
  );
  return { root: root2, els: els2, header: header2, win: win2 };
}

let failed2 = 0;
function check2(name, cond, detail = "") {
  if (cond) {
    console.log(`PASS ${name}`);
  } else {
    failed2++;
    console.log(`FAIL ${name}${detail ? `: ${detail}` : ""}`);
  }
}

const enVisit = freshRun({ storedLang: null, browserLanguage: "en-US" });
check2(
  "영어 브라우저 첫 방문은 영어로 시작",
  enVisit.root.lang === "en" &&
    enVisit.els.every((e) => e.textContent === e.attrs["data-en"]),
);

const koVisit = freshRun({ storedLang: null, browserLanguage: "ko-KR" });
check2(
  "한국어 브라우저라도 첫 방문은 영어로 시작",
  koVisit.root.lang === "en" &&
    koVisit.els.every((e) => e.textContent === e.attrs["data-en"]),
);

const enStored = freshRun({ storedLang: "en", browserLanguage: "ko-KR" });
check2(
  "en 저장 후 재방문하면 한국어 브라우저라도 영어",
  enStored.root.lang === "en" &&
    enStored.els.every((e) => e.textContent === e.attrs["data-en"]),
);

const koStored = freshRun({ storedLang: "ko", browserLanguage: "en-US" });
check2(
  "ko 저장값이 남아 있어도 영어로 시작",
  koStored.root.lang === "en" &&
    koStored.els.every((e) => e.textContent === e.attrs["data-en"]),
);

if (failed2) {
  console.log(`\n${failed2} failed`);
  process.exit(1);
}
console.log("초기 언어 선택과 저장값 우선순위 검증 통과");
