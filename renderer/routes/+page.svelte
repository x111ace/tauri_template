<script lang="ts">
    // @ts-nocheck
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    
    // This component's only job is to redirect to the real entry page
    onMount(() => {
        goto('/entry', { replaceState: true });
    });
</script>

<!-- Optional: Show a loading message while redirecting -->
<p>Loading...</p> 