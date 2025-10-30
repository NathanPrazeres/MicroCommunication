/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useEffect, useState } from "react";
import { useKeycloak } from "@react-keycloak/web";
import type { UserDto } from "@/models/dto";
import { UsersAPI } from "@/api/users";

interface UserContextType {
	user: UserDto | null;
	setUser: React.Dispatch<React.SetStateAction<UserDto | null>>;
	token: string | null;
	loading: boolean;
	logOut: () => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { keycloak, initialized } = useKeycloak();
	const [user, setUser] = useState<UserDto | null>(null);
	const [token, setToken] = useState<string | null>(null);
	const [loading, setLoading] = useState(true);

	// Update token whenever keycloak token changes
	useEffect(() => {
		if (initialized && keycloak.token) {
			setToken(keycloak.token);
		} else {
			setToken(null);
		}
	}, [keycloak.token, initialized]);

	// Listen for token refresh events
	useEffect(() => {
		if (!initialized) return;

		const onTokensUpdated = () => {
			setToken(keycloak.token ?? null);
		};

		keycloak.onAuthRefreshSuccess = onTokensUpdated;
		keycloak.onAuthSuccess = onTokensUpdated;

		return () => {
			keycloak.onAuthRefreshSuccess = undefined;
			keycloak.onAuthSuccess = undefined;
		};
	}, [keycloak, initialized]);

	useEffect(() => {
		if (!initialized) return;

		const fetchUser = async () => {
			if (keycloak.authenticated && keycloak.token) {
				try {
					const userData = await UsersAPI.getCurrentUser(keycloak.token);
					setUser(userData);
				} catch {
					// User doesn't exist
					try {
						const newUser = await UsersAPI.createUser(keycloak.token);
						setUser(newUser);
					} catch (error) {
						console.error("Failed to fetch user:", error);
						setUser(null);
					}
				}
			} else {
				setUser(null);
			}
			setLoading(false);
		};

		fetchUser();
	}, [keycloak.authenticated, keycloak.token, initialized]);

	const logOut = () => {
		keycloak.logout({
			redirectUri: window.location.origin + "/",
		});
	};

	return (
		<UserContext.Provider
			value={{
				user,
				setUser,
				token,
				loading,
				logOut,
			}}
		>
			{children}
		</UserContext.Provider>
	);
};

export const useUser = () => {
	const context = useContext(UserContext);
	if (!context) throw new Error("useUser must be used within a UserProvider");
	return context;
};
