// @electron-gui/src/renderer/lib/mouseEffects.ts

interface PixelTrailConfig {
    explosionCount?: number;
    explosionRadius?: number;
}

export function pixelExplosion(node: HTMLElement, config: PixelTrailConfig = {}) {
    const finalConfig = {
        explosionCount: config.explosionCount ?? 12,
        explosionRadius: config.explosionRadius ?? 50
    };

    const handleClick = (event: MouseEvent) => {
        if (event.button !== 0) return; // Only on left click

        // Prevent effect if clicking on something that is draggable
        const targetElement = event.target as HTMLElement;
        if (targetElement.closest('[style*="cursor: grab"]')) {
            return;
        }

        const x = event.clientX;
        const y = event.clientY;

        for (let i = 0; i < finalConfig.explosionCount; i++) {
            const trailElement = document.createElement('div');
            document.body.appendChild(trailElement);
            
            trailElement.style.cssText = `
                position: absolute;
                width: 8px;
                height: 8px;
                background: #00ffff;
                border-radius: 0;
                pointer-events: none;
                opacity: 1;
                z-index: 1000;
                left: ${x - 4}px;
                top: ${y - 4}px;
                transition: all 0.3s ease-out;
            `;
            
            const angle = (i / finalConfig.explosionCount) * Math.PI * 2;
            const distance = Math.random() * finalConfig.explosionRadius + 20;
            const offsetX = Math.cos(angle) * distance;
            const offsetY = Math.sin(angle) * distance;
            
            setTimeout(() => {
                trailElement.style.left = `${x + offsetX - 4}px`;
                trailElement.style.top = `${y + offsetY - 4}px`;
                trailElement.style.opacity = '0';
                trailElement.style.transform = 'scale(0.5)';
            }, 10);
            
            setTimeout(() => {
                trailElement.remove();
            }, 300);
        }
    };

    node.addEventListener('mousedown', handleClick);

    return {
        destroy() {
            node.removeEventListener('mousedown', handleClick);
        }
    };
} 