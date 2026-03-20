import { ChatAppResponse } from "../../api";

export type HistoryMetaData = { id: string; title: string; timestamp: number };
export type Answers = [user: string, response: ChatAppResponse][];
export type HistoryItemData = { answers: Answers; folder_id?: string };

export const enum HistoryProviderOptions {
    None = "none",
    IndexedDB = "indexedDB",
    CosmosDB = "cosmosDB"
}

export interface IHistoryProvider {
    getProviderName(): HistoryProviderOptions;
    resetContinuationToken(): void;
    getNextItems(count: number, idToken?: string): Promise<HistoryMetaData[]>;
    addItem(id: string, answers: Answers, idToken?: string, folder_id?: string): Promise<void>;
    getItem(id: string, idToken?: string): Promise<HistoryItemData | null>;
    deleteItem(id: string, idToken?: string): Promise<void>;
}
