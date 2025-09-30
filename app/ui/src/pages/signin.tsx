import { useKeycloak } from '@react-keycloak/web';
import { useEffect } from "react";
import { useNavigate } from "react-router";
import { Spinner } from "@/components/ui/spinner";

export const SignInPage = () => {
  const { keycloak, initialized } = useKeycloak();
  const navigate = useNavigate();

  useEffect(() => {
    if (!initialized) return;

    // If already authenticated, redirect to home
    if (keycloak.authenticated) {
      navigate('/');
      return;
    }

    // Redirect to Keycloak login page
    keycloak.login({
      redirectUri: window.location.origin + '/',
    });
  }, [keycloak, initialized, navigate]);

  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <Spinner className="size-16" />
      <p className="text-muted-foreground">Redirecting to login...</p>
    </div>
  );
};