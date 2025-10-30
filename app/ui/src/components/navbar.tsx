import { Button } from "@/components/ui/button";
import { ArrowLeft, Home, Moon, Sun, WifiOff } from "lucide-react";
import { useTheme } from "@/components/ui/theme-provider";
import { useUser } from "@/context/user-context";
import { useRoom } from "@/context/room-context";
import { useChatWs } from "@/context/websocket-context";
import { useLocation, useNavigate } from "react-router";
import { ReadyState } from "react-use-websocket";

export const Navbar = () => {
  const { theme, setTheme } = useTheme();
  const { user, logOut } = useUser();
  const { room, setRoom } = useRoom();
  const { readyState, reconnect } = useChatWs();
  const navigate = useNavigate();
  const location = useLocation();

  const signOut = () => {
    setRoom(null);
    logOut();
    goBack();
  };

  const goBack = (endpoint: "/" | "/rooms" = "/") => {
    setRoom(null);
    if (location.pathname == endpoint) return;
    navigate(endpoint);
  };

  const goTo = (endpoint: string) => {
    setRoom(null);
    if (location.pathname == endpoint) return;
    navigate(endpoint);
  };

  const authForm = () => {
    if (user) {
      return (
        <>
          <Button size="sm" onClick={() => goTo("/profile")}>
            Profile
          </Button>
          <Button variant="outline" size="sm" onClick={signOut}>
            Sign Out
          </Button>
        </>
      )
    } else {
      return (
        <>
          <Button variant="outline" size="sm" onClick={() => goTo("/signin")}>
            Sign In
          </Button>
          <Button size="sm" onClick={() => goTo("/signup")}>
            Sign Up
          </Button>
        </>
      )
    }
  };

  // Show reconnect button if user is logged in and WebSocket is not connected
  const showReconnect = user && readyState !== ReadyState.OPEN;

  return (
    <>
      {/* Navbar */}
      <header className="w-full px-2 md:px-5 py-2 bg-background z-50 relative">
        <div className="flex items-center border-b border-border justify-between px-4 py-3">
          {/* Left side - Navigation */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => goBack(room ? "/rooms" : "/")}
            >
              {room ?
              <ArrowLeft className="h-5 w-5" />
              :
              <Home className="h-5 w-5" />
              }
            </Button>
            <h1 className="text-xl font-semibold">Chat App</h1>
          </div>

          {/* Right side - Reconnect + Auth + Theme */}
          <div className="flex items-center gap-2">
            {showReconnect && (
              <Button
                variant="destructive"
                size="sm"
                onClick={reconnect}
                className="flex items-center gap-2 hover:opacity-80 hover:scale-105 transition-all cursor-pointer"
              >
                <WifiOff className="h-4 w-4" />
                <span className="hidden sm:inline">Reconnect</span>
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() =>
                setTheme(theme === "light" ? "dark" : "light")
              }
            >
              {theme === "light" ? (
                <Moon className="h-5 w-5" />
              ) : (
                <Sun className="h-5 w-5" />
              )}
            </Button>
            {authForm()}
          </div>
        </div>
      </header>
    </>
  );
};