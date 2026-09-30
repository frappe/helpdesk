<template>
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- cuts a gap around the slash so any background shows through it -->
    <mask
      :id="maskId"
      maskUnits="userSpaceOnUse"
      x="0"
      y="0"
      width="16"
      height="16"
    >
      <rect width="16" height="16" fill="white" />
      <path
        d="M1.5 1.5L14.5 14.5"
        stroke="black"
        stroke-width="3"
        stroke-linecap="round"
      />
    </mask>
    <path
      d="M14.3571 4.11463C15.2627 5.02037 15.3379 6.46463 14.5304 7.45889L11.0218 11.7782C10.8612 11.976 10.7534 12.2116 10.709 12.4625L10.4211 14.0915C10.2805 14.888 9.30139 15.1974 8.72926 14.6259L5.42782 11.3245L3.60895 13.1434C3.4137 13.3386 3.0971 13.3386 2.90184 13.1434C2.70677 12.9481 2.70667 12.6315 2.90184 12.4363L4.72071 10.6174L1.37369 7.27037C0.802362 6.69823 1.1117 5.71912 1.90817 5.57856L3.5254 5.29268C3.78193 5.24738 4.0231 5.13661 4.22353 4.9702L8.47445 1.44019C9.46782 0.615802 10.9258 0.683583 11.8387 1.59626L14.3571 4.11463ZM11.1316 2.30336C10.5838 1.75583 9.70918 1.71545 9.1132 2.21014L4.86227 5.73877C4.52813 6.01619 4.12641 6.2026 3.69872 6.27808L2.0808 6.56327L9.43637 13.9175L9.72363 12.2892C9.79752 11.8705 9.977 11.4777 10.245 11.1477L13.7536 6.82843C14.2381 6.23189 14.1934 5.36521 13.65 4.82174L11.1316 2.30336Z"
      fill="currentColor"
      :mask="`url(#${maskId})`"
    />
    <path
      d="M1.5 1.5L14.5 14.5"
      stroke="currentColor"
      stroke-width="1"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
import { useId } from "vue";

// per instance: a hidden icon's mask would blank every icon sharing its id
const maskId = useId();
</script>
