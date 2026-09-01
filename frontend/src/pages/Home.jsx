import Navbar from '../components/layout/Navbar'
import Hero from '../components/home/Hero'
import About from '../components/About'
import Categories from '../components/Categories'
import Footer from '../components/Footer'

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950">
      <Navbar />
      <Hero />
      <About />
      <Categories />
      <Footer />
    </div>
  )
}
