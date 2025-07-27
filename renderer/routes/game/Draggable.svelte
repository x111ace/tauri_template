<script lang="ts">
    import { onMount } from 'svelte';

    let element: HTMLElement;
    let isDragging = false;
    let offsetX: number;
    let offsetY: number;

    function handleMouseDown(e: MouseEvent) {
        if (e.button !== 0) return; // Only left-click
        
        isDragging = true;
        
        const rect = element.getBoundingClientRect();
        
        // This is the key: set the transform to none *before* calculating offsets
        // so that the getBoundingClientRect() is accurate.
        element.style.transform = 'none';
        element.style.left = `${rect.left}px`;
        element.style.top = `${rect.top}px`;
        
        // Now calculate the offset from the true top-left corner
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        
        element.style.cursor = 'grabbing';
    }

    function handleMouseMove(e: MouseEvent) {
        if (!isDragging) return;

        // The new position is the mouse's current position minus the initial offset
        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;

        element.style.left = `${x}px`;
        element.style.top = `${y}px`;
    }

    function handleMouseUp() {
        if (isDragging) {
            isDragging = false;
            element.style.cursor = 'grab';
        }
    }
</script>

<div
    bind:this={element}
    on:mousedown={handleMouseDown}
    style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); cursor: grab; user-select: none;"
    role="button"
    tabindex="0"
>
    <slot></slot>
</div>

<svelte:window on:mousemove={handleMouseMove} on:mouseup={handleMouseUp} /> 