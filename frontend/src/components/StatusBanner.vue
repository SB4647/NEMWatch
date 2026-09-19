<script setup lang="ts">
defineProps<{ loading: boolean; error: string | null }>()
defineEmits<{ retry: [] }>()
</script>
<template>
  <div v-if="loading" class="status-banner" role="status">Loading market data…</div>
  <div v-else-if="error" class="status-banner status-banner--error" role="alert">
    <span>{{ error }}</span><button type="button" @click="$emit('retry')">Try again</button>
  </div>
</template>
