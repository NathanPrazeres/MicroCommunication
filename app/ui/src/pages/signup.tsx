import { useKeycloak } from '@react-keycloak/web';
import { useEffect } from "react";
import { useNavigate } from "react-router";
import { Spinner } from "@/components/ui/spinner";

export const SignUpPage = () => {
  const { keycloak, initialized } = useKeycloak();
  const navigate = useNavigate();

  useEffect(() => {
    if (!initialized) return;

    // If already authenticated, redirect to profile
    if (keycloak.authenticated) {
      navigate('/profile');
      return;
    }

    // Redirect to Keycloak registration page
    keycloak.register({
      redirectUri: window.location.origin + '/register',
    });
  }, [keycloak, initialized, navigate]);

  return (
    <div className="flex flex-col items-center justify-center h-screen gap-4">
      <Spinner className="size-16" />
      <p className="text-muted-foreground">Redirecting to registration...</p>
    </div>
  );
};