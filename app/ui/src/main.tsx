import { createRoot } from 'react-dom/client'
import '@/index.css'
import { loadConfig } from './config'

loadConfig().then(() => {
  // Import everything AFTER config is loaded
  Promise.all([
    import('@/App.tsx'),
    import('@/components/ui/theme-provider.tsx'),
    import('@/context/room-context.tsx'),
    import('@/context/user-context'),
    import('@/context/websocket-context.tsx'),
    import('@react-keycloak/web'),
    import('react'),
    import('./keycloak')
  ]).then(([
    { default: App },
    { ThemeProvider },
    { RoomProvider },
    { UserProvider },
    { WebSocketProvider },
    { ReactKeycloakProvider },
    { StrictMode },
    { default: keycloak }
  ]) => {
    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <ReactKeycloakProvider
          authClient={keycloak}
		      initOptions={{ enableLogging: true }}
        >
          <ThemeProvider defaultTheme='system' storageKey='vite-ui-theme'>
            <UserProvider>
              <WebSocketProvider>
                <RoomProvider>
                  <App />
                </RoomProvider>
              </WebSocketProvider>
            </UserProvider>
          </ThemeProvider>
        </ReactKeycloakProvider>
      </StrictMode>
    )
  })
})
