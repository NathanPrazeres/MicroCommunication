import { useEffect } from "react";
import { useNavigate } from "react-router";
import { useUser } from "@/context/user-context";
import { UsersAPI } from "@/api/users";
import { Spinner } from "@/components/ui/spinner";

export const RegisterPage = () => {
  const { token, user } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (!token || !user) {
      // Not authenticated yet, wait for Keycloak redirect
      return;
    }

    const createUserProfile = async () => {
      try {
        await UsersAPI.createUser(token);
        // Redirect to profile page
        navigate("/profile");
      } catch (error) {
        console.error("Failed to create user profile:", error);
        navigate("/profile");
      }
    };

    createUserProfile();
  }, [token, user, navigate]);

  return (
    <div className="flex flex-col justify-center items-center h-screen gap-4">
      <Spinner className="size-16" />
      <p className="text-muted-foreground">Setting up your account...</p>
    </div>
  );
};