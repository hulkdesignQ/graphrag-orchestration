import { IHistoryProvider, Answers, HistoryProviderOptions, HistoryMetaData, HistoryItemData } from "./IProvider";

export class NoneProvider implements IHistoryProvider {
    getProviderName = () => HistoryProviderOptions.None;
    resetContinuationToken(): void {
        return;
    }
    async getNextItems(count: number): Promise<HistoryMetaData[]> {
        return [];
    }
    async addItem(id: string, answers: Answers, idToken?: string, folder_id?: string): Promise<void> {
        return;
    }
    async getItem(id: string): Promise<HistoryItemData | null> {
        return null;
    }
    async deleteItem(id: string): Promise<void> {
        return;
    }
}
