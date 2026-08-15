// Debug/QA hook — pinned by ADR-0001 (docs/ADR.md). DO NOT REMOVE.
// The Phase 4 QA harness (Playwright scripted scenarios) asserts against
// window.__game.state. It looks unused in early phases by design.

export interface DebugState {
    scene: string;
    position: { x: number; y: number };
    inventory: Record<string, number>;
    doors: Record<string, string>;
    seed: string;
}

const DEFAULT_SEED = 'jotbeat-default-seed';

const state: DebugState = {
    scene: 'Boot',
    position: { x: 0, y: 0 },
    inventory: {},
    doors: {},
    seed: DEFAULT_SEED,
};

declare global {
    interface Window {
        __game: {
            state: DebugState;
            setSeed: (seed: string) => void;
        };
    }
}

/** Seed resolution order: ?seed= URL param (QA runs) -> default. */
export function getSeed (): string
{
    const param = new URLSearchParams(window.location.search).get('seed');
    state.seed = param && param.length > 0 ? param : DEFAULT_SEED;
    return state.seed;
}

/** Call once before `new Game(...)`. */
export function installDebugHook (): void
{
    window.__game = {
        state,
        setSeed: (seed: string) => { state.seed = seed; },
    };
}

export function setScene (scene: string): void
{
    state.scene = scene;
}

export function setPosition (x: number, y: number): void
{
    state.position.x = Math.round(x * 100) / 100;
    state.position.y = Math.round(y * 100) / 100;
}
