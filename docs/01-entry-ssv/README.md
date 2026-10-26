# 1. The entry: the SSV (SerializedScriptValue) bug

The entry point is **public scene work**: the SerializedScriptValue bug
family (Jordy / zecoxao lineage, public since the 13.04/13.52 hosts).
We did not find it; we ported it, proved it on 14.00, and documented
the exact mechanics as implemented in `poc/poc.html`.

## The bug in one paragraph

`history.replaceState(graph, "")` serializes a JS object graph through
WebKit's `SerializedScriptValue`. The **serializer does not pool
BigInts**; the **deserializer does**. Plant a duplicated reference in
the graph: at deserialization the pool index of the second reference is
written on **2 bytes** but read back on **4** — a controlled `-2`
signed index lands in `MarkedVector::at()`, returning
`m_buffer[-2]`: the **groomed predecessor** of the pool vector. The
predecessor's backing store is shaped (a sea of raw low-48 pointers)
so `m_buffer[-2]` is interpreted as a fake `Uint8Array` cell in
raw-fields mode — a genuine, engine-blessed `Uint8Array` whose vector
points wherever we say. Read/write one byte at a time through the
carrier; redirect its vector between reads, and you have **arbitrary
userland R/W** (`GENUINE-U8-RW-PASS`, `ARBITRARY-READ/WRITE-PASS`).

## The carrier and the groom (the parts that must be measured, not guessed)

- The pointer-carrying object is a **5,000,000-slot function** (~40 MB
  of butterfly). This is the law: 2M failed coverage, 5M works first
  try. The carrier also gives addrof: swap objects into the getter's
  slots and read their pointers out of the serialized symbol string.
- The heap groom (drain buffers, butterfly holes, separator, guard,
  predecessor slab) places the fake cell exactly where the
  deserializer's pool will read. The measured ceiling: everything above
  ~80 MB total dies, so the drain ladder tops out at 512 buffers.
- Source-level reference: `Source/WebCore/bindings/js/SerializedScriptValue.cpp`
  in Sony's own LGPL drop (see `frozen-engine.md`) — the m_objectPool
  asymmetry is visible in the frozen source.

## Why a placement miss is benign

On a miss the page restores the carrier vector, clears the
predecessor, and self-reloads through a proven ladder (drain sizes
512/384/256...). The engine state stays coherent; `SURVIVED-*`
markers prove the process lives on. The only fatal case is running out
of the ~80 MB budget — hence the OOM relief valve note in the pages.

Files: `poc/poc.html` (stage 1), `data/markers.md` (vocabulary),
attribution in `NOTICE.md`.
