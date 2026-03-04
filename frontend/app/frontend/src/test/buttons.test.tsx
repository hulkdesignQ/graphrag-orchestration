import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "./testUtils";

import { ClearChatButton } from "../components/ClearChatButton";
import { HistoryButton } from "../components/HistoryButton";

describe("ClearChatButton", () => {
    it("renders with label", () => {
        renderWithProviders(<ClearChatButton onClick={vi.fn()} />);
        expect(screen.getByText("Clear chat")).toBeInTheDocument();
    });

    it("calls onClick when clicked", async () => {
        const user = userEvent.setup();
        const onClick = vi.fn();
        renderWithProviders(<ClearChatButton onClick={onClick} />);
        await user.click(screen.getByRole("button"));
        expect(onClick).toHaveBeenCalledOnce();
    });

    it("can be disabled", () => {
        renderWithProviders(<ClearChatButton onClick={vi.fn()} disabled />);
        expect(screen.getByRole("button")).toBeDisabled();
    });
});

describe("HistoryButton", () => {
    it("renders with label", () => {
        renderWithProviders(<HistoryButton onClick={vi.fn()} />);
        expect(screen.getByText("Open chat history")).toBeInTheDocument();
    });

    it("can be disabled", () => {
        renderWithProviders(<HistoryButton onClick={vi.fn()} disabled />);
        expect(screen.getByRole("button")).toBeDisabled();
    });
});
