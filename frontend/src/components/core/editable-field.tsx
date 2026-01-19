"use client";
import { Input } from "@/components/ui/input";
import { Controller, useFormContext } from "react-hook-form";

type EditableFieldProps = {
  readonly name: string;
};

export function EditableField({ name }: EditableFieldProps) {
  const { control } = useFormContext();
  return (
    <Controller
      name={name}
      control={control}
      render={({ field }) => <Input {...field} className="h-9 mt-1" />}
    />
  );
}
