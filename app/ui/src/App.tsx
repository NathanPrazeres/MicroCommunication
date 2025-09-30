import '@/App.css'
import { BrowserRouter, Route, Routes } from 'react-router'
import { ChatRoomsPage } from '@/pages/rooms'
import { Navbar } from '@/components/navbar'
import { ErrorPage } from '@/pages/error'
import { HomePage } from '@/pages/home'
import { ProfilePage } from '@/pages/profile'
import { SignInPage } from '@/pages/signin'
import { SignUpPage } from '@/pages/signup'
import { RoomMessagesPage } from '@/pages/messages'
import { ContactsPage } from '@/pages/contacts'
import { RegisterPage } from './pages/register'
import { NewRoomPage } from './pages/new_room'

function App() {
  return (
    <>
      <BrowserRouter>
        <Navbar />
        <Routes>
          {/* User */}
          <Route path="/contacts" element={<ContactsPage />} />
          <Route path='/profile' element={<ProfilePage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Auth */}
          <Route path='/signin' element={<SignInPage />} />
          <Route path='/signup' element={<SignUpPage />} />

          {/* Chat */}
          <Route path='/rooms' element={<ChatRoomsPage />} />
          <Route path='/rooms/new' element={<NewRoomPage />} />
          <Route path='/rooms/:roomId' element={<RoomMessagesPage />} />

          {/* General */}
          <Route path='/' element={<HomePage />} />
          <Route path='*' element={<ErrorPage />} />
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
