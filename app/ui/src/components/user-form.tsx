import type { ReactNode } from "react";
import { Field, FieldGroup, FieldLabel, FieldSeparator } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";

type UserFormProps = {
    title: string;
    submitLabel: string;
    onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
    submitting: boolean;
    size: "xs" | "sm" | "lg" | "xl";
    children: ReactNode;
}

export const UserForm = ({title, submitLabel, onSubmit, submitting, size, children}: UserFormProps) => {
  return (
    <div className={`mx-auto my-8 flex max-w-${size} items-center gap-x-10 rounded-xl bg-white p-6 shadow-lg outline outline-black/5 dark:bg-neutral-800 dark:shadow-none dark:-outline-offset-1 dark:outline-white/10`}>
      <form onSubmit={onSubmit} className="w-full flex flex-col items-center">
        <FieldGroup>
          <Field>
            <FieldLabel className="block text-2xl font-bold">
              {title}
            </FieldLabel>
          </Field>

          <FieldSeparator className="-my-4" />

          {children}

          <Button type="submit" disabled={submitting}>
            {submitting ? <Spinner /> : undefined}
            {submitLabel}
          </Button>
        </FieldGroup>
      </form>
    </div>
  );
};