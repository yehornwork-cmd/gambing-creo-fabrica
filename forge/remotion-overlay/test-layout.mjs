#!/usr/bin/env node
import assert from "node:assert/strict";
import { defaultHeadlineBox, headlineFontSize, headlineLayout, OUTPUT } from "./src/layout.ts";

const box = defaultHeadlineBox();
assert.equal(OUTPUT.width, 1080);
assert.equal(OUTPUT.height, 1920);
assert.deepEqual(box, { x: 162, y: 1056, w: 756, h: 422 });

const pl = ["KRĘĆ I WYGRYWAJ", "GRAJ TERAZ"];
const maxLen = Math.max(...pl.map((s) => s.length));
assert.equal(maxLen, 15);
const expected = Math.max(
  40,
  Math.min(Math.floor((box.w * 0.86) / (maxLen * 0.56)), Math.floor(box.h / 2.35)),
);
assert.equal(headlineFontSize(pl, box), expected);

const lay = headlineLayout(pl, box);
assert.equal(lay.y1, box.y);
assert.equal(lay.y2, box.y + Math.round(box.h * 0.54));
assert.equal(lay.fontSize, expected);

console.log("layout ok", { box, maxLen, fontSize: lay.fontSize, y2: lay.y2 });
