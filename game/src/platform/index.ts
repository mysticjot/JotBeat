//  Platform adapter — the ONLY seam between game code and host wrappers.
//
//  RULE (docs/DECISIONS.md D-0002): game code must NEVER import Electron,
//  Capacitor, or any wrapper API directly. Every platform-specific feature
//  (save files, fullscreen, haptics, ...) goes through this module.
//
//  The WEB implementation below is the default fallback and must always
//  work standalone. Desktop (Electron) and mobile (Capacitor) builds inject
//  their own implementation by calling setPlatformAdapter() before the game
//  boots; game code keeps calling save()/load()/... unchanged.

export interface PlatformAdapter
{
    save (key: string, value: string): void;
    load (key: string): string | null;
    requestFullscreen (): void;
    haptic (ms: number): void;
}

const webAdapter: PlatformAdapter = {
    save (key: string, value: string): void
    {
        localStorage.setItem(`jotbeat:${key}`, value);
    },

    load (key: string): string | null
    {
        return localStorage.getItem(`jotbeat:${key}`);
    },

    requestFullscreen (): void
    {
        if (!document.fullscreenElement)
        {
            void document.documentElement.requestFullscreen?.();
        }
    },

    haptic (ms: number): void
    {
        navigator.vibrate?.(ms);
    },
};

let adapter: PlatformAdapter = webAdapter;

export function setPlatformAdapter (custom: PlatformAdapter): void
{
    adapter = custom;
}

export function save (key: string, value: string): void
{
    adapter.save(key, value);
}

export function load (key: string): string | null
{
    return adapter.load(key);
}

export function requestFullscreen (): void
{
    adapter.requestFullscreen();
}

export function haptic (ms: number): void
{
    adapter.haptic(ms);
}
