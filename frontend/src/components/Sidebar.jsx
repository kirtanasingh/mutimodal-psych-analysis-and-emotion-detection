import { NavLink } from 'react-router-dom'
import { FilePlus2, FileText, LayoutDashboard, LogOut, Users } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const links = [['/', 'Dashboard', LayoutDashboard], ['/patients', 'Patients', Users], ['/sessions/new', 'New session', FilePlus2], ['/reports', 'Reports', FileText]]
  return (
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark"><LayoutDashboard size={17} /></span><span>Clinical Workspace</span></div>
      <nav>{links.map(([to, label, Icon]) => <NavLink key={to} to={to} end={to === '/'}><Icon size={18} /><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-footer"><div className="user-chip"><span className="avatar">{user?.display_name?.[0] || 'C'}</span><span>{user?.display_name || 'Clinician'}<small>{user?.email}</small></span></div><button className="logout-button" onClick={logout} title="Sign out"><LogOut size={17} /></button></div>
    </aside>
  )
}
