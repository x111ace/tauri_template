<script lang="ts">
    // @ts-nocheck
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import './styles/entry-page.css';

    onMount(() => {
        // Notify the backend that the user has reached the entry page
        if (window.tauriAPI) {
            window.tauriAPI.send('notify', 'User has entered the ENTRY page.');
        }
    });

    async function goToGame() {
        await goto('/game');
    }
</script>

<div class="entry-page-container">
    <h1>Hello, World!</h1>
    <button on:click={goToGame} class="centered-button">Enter the Main Page</button>
</div> 