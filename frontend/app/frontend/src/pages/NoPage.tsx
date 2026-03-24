import { type JSX } from "react";
import { Navigate } from "react-router-dom";

export function Component(): JSX.Element {
    return <Navigate to="/" replace />;
}

Component.displayName = "NoPage";
