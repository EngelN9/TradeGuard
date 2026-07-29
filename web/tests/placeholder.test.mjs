import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const pageSource = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");

test("dashboard identifies the non-live research environment", () => {
  assert.match(pageSource, /RESEARCH \/ NOT TRADABLE/);
  assert.match(pageSource, /沒有正式交易、提款、轉帳/);
});

test("dashboard does not present a live control", () => {
  assert.doesNotMatch(pageSource, /make live/);
  assert.doesNotMatch(pageSource, /live order/i);
});
