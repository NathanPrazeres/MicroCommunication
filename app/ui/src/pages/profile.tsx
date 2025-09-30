import { UsersAPI } from "@/api/users";
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import { UserForm } from "@/components/user-form";
import { useUser } from "@/context/user-context";
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router";

export const ProfilePage = () => {
  const [ submitting, setSubmitting ] = useState<boolean>(false);
  const [ bio, setBio ] = useState<string>("");
  const [ error, setError ] = useState<string | null>(null);
  const [ errorField, setErrorField ] = useState<string | null>(null);
  const { user, setUser, token, loading } = useUser();
  const navigate = useNavigate();

  // Redirect users who aren't logged in to do so
  useEffect(() => {
    if (loading) return;
    if (!user) navigate("/signup");

    setBio(user?.bio || "");
  }, [user, loading, navigate]);

  const handleProfileChange = async (e: React.FormEvent) => {
    setSubmitting(true);
    setError(null);
    setErrorField(null);
    e.preventDefault();
    if (bio != user?.bio) {
      if (bio.length > 100) {
        setError("Bio may have no more than 100 characters.");
        setErrorField("bio_input")
        setSubmitting(false);
        return;
      }

      if (!token) {
        console.error("Couldn't get JWT");
        setError("Couldn't get JWT. Please try again.");
        setSubmitting(false);
        return;
      }
      try {
        setUser(await UsersAPI.updateUser(token, bio));
      } catch (error) {
        console.error("Failed to update user:", error);
        setError("Failed to update user. Please try again.");
      }
    }

    setSubmitting(false);
  }

  return (
    <div className="mx-10">
      <UserForm
        title="Profile"
        submitLabel="Save"
        onSubmit={handleProfileChange}
        submitting={submitting}
        size="lg"
      >
        <Field>
          <FieldLabel htmlFor="bio" className="mx-2">
            Edit Bio
          </FieldLabel>
          <Textarea
            id="bio"
            name="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="I love watching movies..."
            className={errorField === "bio_input" ? "border-red-500 ring-2 ring-red-500" : ""}
          />
          <FieldDescription className="flex mx-2">
            Share something about yourself!
          </FieldDescription>
        </Field>

        {error && (
         <div className="mb-2 text-red-600 dark:text-red-400 text-sm">{error}</div>
        )}
      </UserForm>
    </div>
  );
};