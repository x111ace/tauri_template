// Tauri API shim for secure IPC in place of Electron's preload

import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';
import { browser } from '$app/environment';

/**
 * Defines the shape of the Tauri API for IPC.
 */
export interface ITauriAPI {
    send: (channel: string, data?: any) => void;
    receive: (channel: string, func: (...args: any[]) => void) => Promise<() => void>;
}

// Extend the global Window interface
declare global {
    interface Window {
        tauriAPI: ITauriAPI;
    }
}

// Polyfill the tauriAPI on window using Tauri's invoke and event.listen
if (browser) {
    window.tauriAPI = {
        send: (channel: string, data?: any) => {
            // Tauri commands take an object; we use { message: data } for simple usage
            invoke(channel, data !== undefined ? { message: data } : {})
                .catch((e: any) => console.error(`Error invoking command ${channel}:`, e));
        },
        receive: (channel: string, func: (...args: any[]) => void) => {
            // Listen for events from the backend; returns an unlisten function
            return listen(channel, (event: any) => {
                func(event.payload);
            });
        }
    };
} 