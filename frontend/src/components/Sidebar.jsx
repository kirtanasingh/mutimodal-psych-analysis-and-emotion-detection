import { NavLink } from 'react-router-dom'

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">Clinical Workspace</div>
      <nav>
        <NavLink to="/" end>Dashboard</NavLink>
        <NavLink to="/patients">Patients</NavLink>
        <NavLink to="/sessions/new">New Session</NavLink>
      </nav>
    </aside>
  )
}
