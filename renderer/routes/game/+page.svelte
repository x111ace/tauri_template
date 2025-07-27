<script lang="ts">
    // @ts-nocheck
    import Draggable from './Draggable.svelte';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import './styles/game-page.css';

    onMount(() => {
        // Notify the backend that the user has entered the game page
		if (window.tauriAPI) {
			window.tauriAPI.send('notify', 'User has entered the GAME page.');
		}

        const handleKeyDown = async (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                await goto('/entry');
            }
        };
        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
        };
    });

</script>

<Draggable>
    <div class="centered-box">
        <p class="hello-text">hello</p>
    </div>
</Draggable> 