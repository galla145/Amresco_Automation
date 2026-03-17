import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";

import defaultProfile from "../assets/profile.png";
import "./dropdown.css";

export default function AccountDropdown() {
  const navigate = useNavigate();

  const [open, setOpen] = useState(false);
  const [profileImg, setProfileImg] = useState(defaultProfile);
  const [position, setPosition] = useState({ top: 0, left: 0 });

  const iconRef = useRef();

  /* Load saved image */
  useEffect(() => {
    const savedImg = localStorage.getItem("profileImage");
    if (savedImg) setProfileImg(savedImg);
  }, []);

  /* Close on outside click */
  useEffect(() => {
    const handleClick = () => setOpen(false);
    if (open) document.addEventListener("click", handleClick);
    return () => document.removeEventListener("click", handleClick);
  }, [open]);

  /* Calculate dropdown position */
  const toggleDropdown = (e) => {
    e.stopPropagation();

    const rect = iconRef.current.getBoundingClientRect();

    setPosition({
      top: rect.bottom + window.scrollY + 5,
      left: rect.right - 180, // width of dropdown
    });

    setOpen(!open);
  };

  /* Image upload (fixed version) */
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        localStorage.setItem("profileImage", reader.result);
        setProfileImg(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/signin");
  };

  return (
    <>
      {/* PROFILE ICON */}
      <img
        ref={iconRef}
        src={profileImg}
        alt="profile"
        className="profile-icon"
        onClick={toggleDropdown}
      />

      {/* PORTAL DROPDOWN */}
      {open &&
        createPortal(
          <div
            className="profile-dropdown portal"
            style={{
              position: "absolute",
              top: position.top,
              left: position.left,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <label className="upload-photo">
              Change Photo
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
              />
            </label>

            <div onClick={() => navigate("/profile")}>Profile</div>
            <div onClick={() => navigate("/settings")}>Settings</div>

            <div className="logout" onClick={handleLogout}>
              Logout
            </div>
          </div>,
          document.body
        )}
    </>
  );
}