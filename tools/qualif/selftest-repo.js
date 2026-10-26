#!/usr/bin/env node
/*
 * selftest-repo.js -- offline coherence checks for the repository.
 * Run before touching a console:   node tools/qualif/selftest-repo.js
 *
 * Verifies that the shipped pieces agree with each other:
 *   1. the 3 exploit pages parse and their <script> is valid JS
 *      (syntax-checked with new Function, no execution);
 *   2. the stub CSV and the live table embedded in the workshop console
 *      agree byte-exact on all 298 entries;
 *   3. the gadget tables in the page and in extract-gadgets.py agree;
 *   4. nothing internal leaked into any shipped text file
 *      (private IPs, run-numbered names, internal jargon, accents).
 * Exits non-zero on the first failed family; prints UNIT-PASS lines.
 */
"use strict";

var fs = require("fs");
var path = require("path");

var REPO = path.join(__dirname, "..", "..");
var fails = 0;

function ok(name, cond, detail) {
    if (cond) {
        console.log("UNIT-PASS " + name + (detail ? " " + detail : ""));
    } else {
        console.log("UNIT-FAIL " + name + (detail ? " " + detail : ""));
        fails++;
    }
}

function read(p) {
    return fs.readFileSync(path.join(REPO, p), "utf8");
}

// ---- 1. the pages parse ------------------------------------------------
["poc/poc.html", "tools/workshop/console.html", "tools/workshop/kex-aio.html"]
    .forEach(function (p) {
        var html = read(p);
        var m = html.match(/<script>([\s\S]*)<\/script>/);
        ok("page-script-present " + p, !!m);
        if (!m) return;
        var syntaxFail = null;
        try {
            new Function(m[1]);      // parse only, never executed
        } catch (e) {
            syntaxFail = e.message;
        }
        ok("page-script-parses " + p, !syntaxFail, syntaxFail || "");
    });

// ---- 2. stub CSV vs the live console table ------------------------------
(function () {
    var page = read("tools/workshop/console.html");
    var m = page.match(/var STUB_TABLE = \{([^}]*)\}/);
    ok("console-stub-table-present", !!m);
    if (!m) return;
    var table = {};
    m[1].split(",").forEach(function (part) {
        var kv = part.split(":");
        table[kv[0].trim().replace(/"/g, "")] = parseInt(kv[1], 10);
    });
    var entries = Object.keys(table).length;
    ok("console-stub-table-size", entries === 298, "entries=" + entries);

    var lines = read("data/syscalls/stubs-1400.csv").trim().split("\n");
    ok("stub-csv-header", lines[0].indexOf("nr,") === 0);
    var hits = {};
    lines.slice(1).forEach(function (l) {
        var c = l.split(",");
        var nr = c[0], off = parseInt(c[2], 10);
        (hits[nr] = hits[nr] || []).push(off);
    });
    var total = lines.length - 1;
    ok("stub-csv-total-hits", total === 302, "hits=" + total);
    var mismatch = 0, missing = 0;
    Object.keys(table).forEach(function (nr) {
        var offs = hits[nr];
        if (!offs) { missing++; return; }
        if (offs.indexOf(table[nr]) === -1) mismatch++;
    });
    ok("stub-csv-matches-live-table", mismatch === 0 && missing === 0,
       "mismatch=" + mismatch + " missing=" + missing);
})();

// ---- 3. gadget tables agree ---------------------------------------------
(function () {
    var page = read("poc/poc.html");
    var m = page.match(/var R4_GAD = \[([\s\S]*?)\];/);
    ok("page-gadget-table-present", !!m);
    if (!m) return;
    var pageGadgets = {};
    m[1].split("\n").forEach(function (l) {
        var g = l.match(/\["([A-Z0-9_]+)",\s*(0x[0-9a-f]+)/);
        if (g) pageGadgets[g[1]] = parseInt(g[2], 16);
    });
    ok("page-gadget-count", Object.keys(pageGadgets).length === 15,
       "count=" + Object.keys(pageGadgets).length);

    var tool = read("tools/extraction/extract-gadgets.py");
    var toolGadgets = {};
    tool.split("\n").forEach(function (l) {
        var g = l.match(/\("([A-Z0-9_]+)",\s*(0x[0-9a-f]+)/);
        if (g) toolGadgets[g[1]] = parseInt(g[2], 16);
    });
    var agree = Object.keys(pageGadgets).every(function (k) {
        return toolGadgets[k] === pageGadgets[k];
    });
    ok("gadget-tables-agree", agree);
})();

// ---- 4. nothing internal leaked -----------------------------------------
(function () {
    var patterns = [
        [/\b192\.168\.[0-9]+\.[0-9]+\b/, "private-IP"],
        [/\brun1[0-9]\b|\bRUN1[0-9]\b/, "run-numbered-name"],
        [/\bboss\b/i, "internal-jargon"],
        [/\bAGENT-[A-Z]/, "internal-jargon"],
        (function () {
            var acc = [];
            for (var i = 0xA0; i <= 0x17F; i++) {
                var ch = String.fromCharCode(i);
                if (/[À-ÿŸœ]/.test(ch)) acc.push(ch);
            }
            return [new RegExp("[" + acc.join("") + "]"), "accented-char"];
        })()
    ];
    var files = [
        "README.md", "STATUS.md", "CHANGELOG.md", "NOTICE.md",
        "REPRODUCE.md", "CONTRIBUTING.md", "index.html",
        "poc/poc.html", "tools/workshop/console.html",
        "tools/workshop/kex-aio.html", "tools/workshop/boot.html",
        "tools/host/server.py", "tools/host/bridge.py",
        "tools/host/start.bat", "tools/host/start.sh",
        "tools/extraction/extract-stubs.py",
        "tools/extraction/extract-gadgets.py",
        "tools/extraction/dump-libkernel.md",
        "extraction/README.md",
        "data/markers.md", "data/offsets/webkit-1400.md",
        "data/offsets/kernel-1400.md", "data/syscalls/README.md",
        "data/syscalls/DANGEROUS.md", "data/syscalls/gates-1400.csv",
        "docs/01-entry-ssv/README.md", "docs/01-entry-ssv/frozen-engine.md",
        "docs/02-userland-chain/README.md",
        "docs/03-syscall-surface/README.md",
        "docs/04-terrain-map/README.md",
        "docs/05-audits/aio-kex.md", "docs/05-audits/ipmimgr-622.md",
        "docs/05-audits/orbis-idt-wrap8.md", "docs/05-audits/bnet-n1.md",
        "docs/05-audits/sandbox-escape.md", "docs/05-audits/dmem-gates.md",
        "docs/05-audits/audit-consolidated.md",
        "docs/05-audits/remote-play.md",
        "docs/06-negative-results.md", "docs/07-next-leads.md"
    ];
    files.forEach(function (f) {
        var text;
        try { text = read(f); } catch (e) { ok("leak-sweep " + f, false, "missing"); return; }
        patterns.forEach(function (p) {
            var hit = text.match(p[0]);
            ok("leak-sweep " + f + " " + p[1], !hit,
               hit ? JSON.stringify(hit[0]) : "");
        });
    });
})();

if (fails) {
    console.log("SELFTEST-FAIL failures=" + fails);
    process.exit(1);
}
console.log("SELFTEST-PASS all units green");
