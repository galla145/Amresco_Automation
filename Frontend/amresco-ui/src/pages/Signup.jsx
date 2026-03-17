import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "../services/supabaseClient";

import logo from "../assets/logo.png";
import hero from "../assets/hero.png";

import "./signin.css";

export default function Signup(){

  const navigate = useNavigate();

  const [email,setEmail] = useState("");
  const [password,setPassword] = useState("");
  const [confirmPassword,setConfirmPassword] = useState("");
  const [loading,setLoading] = useState(false);

  const handleSignup = async (e) => {

    e.preventDefault();

    /* Check if passwords match */
    if(password !== confirmPassword){
      alert("Passwords do not match");
      return;
    }

    setLoading(true);

    const { error } = await supabase.auth.signUp({
      email: email,
      password: password
    });

    if(error){
      alert(error.message);
      setLoading(false);
      return;
    }

    alert("Account created successfully! Please sign in.");

    navigate("/signin");
  };

  return(

    <div className="container">

      <header className="navbar">
        <div className="nav-left">
          <img src={logo} alt="logo"/>
        </div>
      </header>

      <section className="signin-section">

        <div className="signin-left">

          <h1>
            Create Your <br/>
            <span>AMRESCO Account</span>
          </h1>

          <p>
            Sign up to start analyzing Excel data
            with AI-powered automation.
          </p>

          <div className="signin-card">

            <h3>Create Account</h3>

            <form onSubmit={handleSignup}>

              <input
                type="email"
                placeholder="Email Address"
                value={email}
                onChange={(e)=>setEmail(e.target.value)}
                required
              />

              <input
                type="password"
                placeholder="New Password"
                value={password}
                onChange={(e)=>setPassword(e.target.value)}
                required
              />

              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e)=>setConfirmPassword(e.target.value)}
                required
              />

              <button className="login-btn">
                {loading ? "Creating..." : "Create Account"}
              </button>

            </form>

            <p className="signup-link">
              Already have an account?{" "}
              <span onClick={()=>navigate("/signin")}>
                Sign In
              </span>
            </p>

          </div>

        </div>

        <div className="signin-right">
          <img src={hero} className="hero-img" alt="hero"/>
        </div>

      </section>

    </div>
  );
}