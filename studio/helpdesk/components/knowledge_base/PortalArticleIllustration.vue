<template>
  <!-- Decorative: an article that writes itself, with the next draft behind it. -->
  <div class="article-illo" aria-hidden="true">
    <div class="article-illo-draft" />
    <div class="article-illo-card">
      <div class="article-illo-line" />
      <div class="article-illo-line" />
      <div class="article-illo-line" />
    </div>
  </div>
</template>

<style>
/* Light values are the handoff's suggestions; only dark was designed. */
.article-illo {
  --illo-ease: cubic-bezier(0.2, 0.8, 0.2, 1);
  --illo-card: #f1f1f1;
  --illo-card-hover: #ececec;
  /* Not in the handoff: the light card needs an edge against white. */
  --illo-card-outline: #e2e2e2;
  --illo-line-strong: #cfcfcf;
  --illo-line: #dddddd;
  --illo-dash: #d6d6d6;
  --illo-dash-hover: #c4c4c4;
  --illo-lift: 0 14px 30px rgba(0, 0, 0, 0.1);
  position: relative;
  width: 92px;
  height: 96px;
}
[data-theme="dark"] .article-illo {
  --illo-card: #242424;
  --illo-card-hover: #282828;
  --illo-card-outline: transparent;
  --illo-line-strong: #444444;
  --illo-line: #363636;
  --illo-dash: #2e2e2e;
  --illo-dash-hover: #3a3a3a;
  --illo-lift: 0 14px 30px rgba(0, 0, 0, 0.5);
}
.article-illo-draft {
  position: absolute;
  left: 18px;
  top: 0;
  width: 70px;
  height: 88px;
  box-sizing: border-box;
  border: 1.5px dashed var(--illo-dash);
  border-radius: 9px;
  transition: transform 450ms var(--illo-ease), border-color 300ms;
}
.article-illo-card {
  position: absolute;
  left: 4px;
  top: 8px;
  width: 70px;
  height: 88px;
  box-sizing: border-box;
  padding: 14px 12px;
  background: var(--illo-card);
  outline: 1px solid var(--illo-card-outline);
  outline-offset: -1px;
  border-radius: 9px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  transition: transform 450ms var(--illo-ease),
    box-shadow 450ms var(--illo-ease), background 300ms;
}
.article-illo-line {
  animation: 4.8s var(--illo-ease) infinite;
}
.article-illo-line:nth-child(1) {
  height: 6px;
  width: 70%;
  background: var(--illo-line-strong);
  border-radius: 3px;
  animation-name: article-illo-l1;
}
.article-illo-line:nth-child(2) {
  height: 4px;
  width: 100%;
  background: var(--illo-line);
  border-radius: 2px;
  animation-name: article-illo-l2;
}
.article-illo-line:nth-child(3) {
  height: 4px;
  width: 45%;
  background: var(--illo-line);
  border-radius: 2px;
  animation-name: article-illo-l3;
}
.article-illo:hover .article-illo-card {
  transform: translate(-4px, -4px) rotate(-3deg);
  background: var(--illo-card-hover);
  box-shadow: var(--illo-lift);
}
.article-illo:hover .article-illo-draft {
  transform: translate(10px, -2px) rotate(6deg);
  border-color: var(--illo-dash-hover);
}
@keyframes article-illo-l1 {
  0% {
    width: 0;
    opacity: 1;
  }
  12% {
    width: 70%;
  }
  88% {
    width: 70%;
    opacity: 1;
  }
  96%,
  100% {
    width: 70%;
    opacity: 0;
  }
}
@keyframes article-illo-l2 {
  0%,
  12% {
    width: 0;
    opacity: 1;
  }
  30% {
    width: 100%;
  }
  88% {
    width: 100%;
    opacity: 1;
  }
  96%,
  100% {
    width: 100%;
    opacity: 0;
  }
}
@keyframes article-illo-l3 {
  0%,
  30% {
    width: 0;
    opacity: 1;
  }
  40% {
    width: 45%;
  }
  88% {
    width: 45%;
    opacity: 1;
  }
  96%,
  100% {
    width: 45%;
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .article-illo-line {
    animation: none;
  }
}
</style>
