<script lang="ts">
    // @ts-nocheck
    import '$lib/api';
    import { pixelExplosion } from '$lib/mouseEffects';
</script>

<div use:pixelExplosion style="height: 100vh; width: 100vw;">
    <slot />
</div> 