import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase, User, AuthUser } from '@/lib/supabase'
import { Session } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  authUser: AuthUser | null
  session: Session | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  signInWithGitHub: () => Promise<void>
  signInWithEmail: (email: string, password: string) => Promise<void>
  signUpWithEmail: (email: string, password: string, name?: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    // Try to load user from localStorage on initialization
    try {
      const cachedUser = localStorage.getItem('vibecheck_user')
      return cachedUser ? JSON.parse(cachedUser) : null
    } catch {
      return null
    }
  })
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(() => {
    // If we have cached user data, start with loading false for instant display
    try {
      const cachedUser = localStorage.getItem('vibecheck_user')
      return !cachedUser
    } catch {
      return true
    }
  })

  // Helper function to cache user data
  const cacheUser = (userData: User | null) => {
    try {
      if (userData) {
        localStorage.setItem('vibecheck_user', JSON.stringify(userData))
      } else {
        localStorage.removeItem('vibecheck_user')
      }
    } catch (error) {
      console.error('Error caching user data:', error)
    }
  }

  useEffect(() => {
    // Set a shorter timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      console.log('Auth timeout - setting loading to false')
      setLoading(false)
    }, 5000) // 5 second timeout

    let isMounted = true

    // Get initial session with better error handling
    const initializeAuth = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Error getting session:', error)
          if (isMounted) {
            setLoading(false)
            clearTimeout(timeout)
          }
          return
        }

        if (isMounted) {
          setSession(session)
          if (session?.user) {
            setAuthUser(session.user as AuthUser)
            // Don't await this to avoid blocking the UI
            fetchUserProfile(session.user.id)
          } else {
            setLoading(false)
            clearTimeout(timeout)
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error)
        if (isMounted) {
          setLoading(false)
          clearTimeout(timeout)
        }
      }
    }

    initializeAuth()

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!isMounted) return

      setSession(session)
      if (session?.user) {
        setAuthUser(session.user as AuthUser)
        // Don't await this to avoid blocking the UI
        fetchUserProfile(session.user.id)
      } else {
        setAuthUser(null)
        setUser(null)
        cacheUser(null)
        setLoading(false)
        clearTimeout(timeout)
      }
    })

    return () => {
      isMounted = false
      subscription.unsubscribe()
      clearTimeout(timeout)
    }
  }, [])

  const fetchUserProfile = async (userId: string) => {
    try {
      // Check if we already have the user data cached
      if (user && user.id === userId) {
        setLoading(false)
        return
      }

      // Add timeout for the database query
      const queryPromise = supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single()

      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Query timeout')), 3000)
      )

      const { data, error } = await Promise.race([queryPromise, timeoutPromise]) as any

      if (error) {
        // If user doesn't exist, create them
        if (error.code === 'PGRST116') {
          await createUserProfile(userId)
          return
        }
        console.error('Error fetching user profile:', error)
        setLoading(false)
        return
      }

      setUser(data)
      cacheUser(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching user profile:', error)
      setLoading(false)
    }
  }

  const createUserProfile = async (userId: string) => {
    try {
      const { data: authUser } = await supabase.auth.getUser()
      if (!authUser.user) {
        setLoading(false)
        return
      }

      const userData = {
        id: userId,
        email: authUser.user.email || '',
        name: authUser.user.user_metadata?.name || authUser.user.user_metadata?.full_name,
        github_username: authUser.user.user_metadata?.user_name || authUser.user.user_metadata?.preferred_username,
      }

      // Add timeout for the insert query
      const insertPromise = supabase
        .from('users')
        .insert(userData)
        .select()
        .single()

      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Insert timeout')), 3000)
      )

      const { data, error } = await Promise.race([insertPromise, timeoutPromise]) as any

      if (error) {
        console.error('Error creating user profile:', error)
        setLoading(false)
        return
      }

      setUser(data)
      cacheUser(data)
      setLoading(false)
    } catch (error) {
      console.error('Error creating user profile:', error)
      setLoading(false)
    }
  }

  const signInWithGoogle = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/`,
        },
      })
      if (error) throw error
    } catch (error) {
      console.error('Error signing in with Google:', error)
      throw error
    }
  }

  const signInWithGitHub = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: `${window.location.origin}/`,
        },
      })
      if (error) throw error
    } catch (error) {
      console.error('Error signing in with GitHub:', error)
      throw error
    }
  }

  const signInWithEmail = async (email: string, password: string) => {
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) throw error
    } catch (error) {
      console.error('Error signing in with email:', error)
      throw error
    }
  }

  const signUpWithEmail = async (email: string, password: string, name?: string) => {
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name: name || '',
          }
        }
      })
      if (error) throw error
    } catch (error) {
      console.error('Error signing up with email:', error)
      throw error
    }
  }

  const signOut = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
      
      // Clear cached user data
      cacheUser(null)
      setUser(null)
      setAuthUser(null)
    } catch (error) {
      console.error('Error signing out:', error)
      throw error
    }
  }

  const value = {
    user,
    authUser,
    session,
    loading,
    signInWithGoogle,
    signInWithGitHub,
    signInWithEmail,
    signUpWithEmail,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
