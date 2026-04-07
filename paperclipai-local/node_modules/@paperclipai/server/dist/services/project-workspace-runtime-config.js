function isRecord(value) {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}
function cloneRecord(value) {
    return isRecord(value) ? { ...value } : null;
}
function readDesiredState(value) {
    return value === "running" || value === "stopped" ? value : null;
}
export function readProjectWorkspaceRuntimeConfig(metadata) {
    const raw = isRecord(metadata?.runtimeConfig) ? metadata.runtimeConfig : null;
    if (!raw)
        return null;
    const config = {
        workspaceRuntime: cloneRecord(raw.workspaceRuntime),
        desiredState: readDesiredState(raw.desiredState),
    };
    const hasConfig = config.workspaceRuntime !== null || config.desiredState !== null;
    return hasConfig ? config : null;
}
export function mergeProjectWorkspaceRuntimeConfig(metadata, patch) {
    const nextMetadata = isRecord(metadata) ? { ...metadata } : {};
    const current = readProjectWorkspaceRuntimeConfig(metadata) ?? {
        workspaceRuntime: null,
        desiredState: null,
    };
    if (patch === null) {
        delete nextMetadata.runtimeConfig;
        return Object.keys(nextMetadata).length > 0 ? nextMetadata : null;
    }
    const nextConfig = {
        workspaceRuntime: patch.workspaceRuntime !== undefined ? cloneRecord(patch.workspaceRuntime) : current.workspaceRuntime,
        desiredState: patch.desiredState !== undefined ? readDesiredState(patch.desiredState) : current.desiredState,
    };
    if (nextConfig.workspaceRuntime === null && nextConfig.desiredState === null) {
        delete nextMetadata.runtimeConfig;
    }
    else {
        nextMetadata.runtimeConfig = nextConfig;
    }
    return Object.keys(nextMetadata).length > 0 ? nextMetadata : null;
}
//# sourceMappingURL=project-workspace-runtime-config.js.map