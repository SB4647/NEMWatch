<script setup lang="ts">
import type { ConnectionState } from '../api/live'
defineProps<{ state: ConnectionState }>()
</script>
<template><p class="live-status" :data-state="state" role="status"><span aria-hidden="true"></span>Live updates: {{ state }}</p></template>
