interface PageHeadingProps {
  title: string;
  description?: string;
}

export default function PageHeading({
  title,
  description,
}: Readonly<PageHeadingProps>) {
  return (
    <>
      {title || description ? (
        <div className="space-y-1 capitalize">
          {title && (
            <h1 className="text-2xl font-bold tracking-tight ">{title}</h1>
          )}
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      ) : null}
    </>
  );
}
