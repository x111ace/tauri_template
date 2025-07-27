import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: 'index.html',
			precompress: false,
			strict: true
		}),
		alias: {
			'$lib': 'renderer/lib'
		},
		files: {
			assets: 'renderer/static',
			appTemplate: 'renderer/app.html',
			routes: 'renderer/routes',
			lib: 'renderer/lib'
		},
		// Prevents conflicts with Electron's 'app' module
		appDir: 'internal'
	}
};

export default config; 