import {
    DocumentPdf24Regular,
    Document24Regular,
    Table24Regular,
    SlideText24Regular,
    Code24Regular,
    Image24Regular,
    Attach24Regular,
} from "@fluentui/react-icons";

const EXT_ICON: Record<string, React.ReactElement> = {
    pdf: <DocumentPdf24Regular />,
    docx: <Document24Regular />,
    txt: <Document24Regular />,
    md: <Document24Regular />,
    xlsx: <Table24Regular />,
    pptx: <SlideText24Regular />,
    json: <Code24Regular />,
    html: <Code24Regular />,
    png: <Image24Regular />,
    jpg: <Image24Regular />,
    jpeg: <Image24Regular />,
    bmp: <Image24Regular />,
    svg: <Image24Regular />,
    tiff: <Image24Regular />,
    heic: <Image24Regular />,
};

const DEFAULT_ICON = <Attach24Regular />;

export const FileIcon = ({ filename }: { filename: string }) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    return EXT_ICON[ext] ?? DEFAULT_ICON;
};
