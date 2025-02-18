import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { CountryDropdown, RegionDropdown } from "react-country-region-selector";
import {
  Button,
  Card,
  Container,
  Row,
  Col,
  ListGroup,
  ListGroupItem,
  Form,
  FormGroup,
  Input,
  Modal,
  ModalHeader,
  ModalBody,
  ModalFooter,
} from "reactstrap";
import { FaEdit, FaSignOutAlt } from "react-icons/fa";
import DemoNavbar from "components/Navbars/DemoNavbar.js";
import SimpleFooter from "components/Footers/SimpleFooter.js";

const Profile = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState({});
  const [resumes, setResumes] = useState([]);
  const [error, setError] = useState("");
  const [editModal, setEditModal] = useState(false);
  const [editForm, setEditForm] = useState({
    username: "",
    email: "",
    bio: "",
    profile_picture: null,
  });
  const [country, setCountry] = useState("");
  const [region, setRegion] = useState("");

  // ✅ Fetch user profile data
  // ✅ Define fetchUserProfile function before using it
  const fetchUserProfile = async () => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");

    if (!token) {
      navigate("/login-page");
      return;
    }

    try {
      const response = await fetch("http://localhost:8000/api/profile/", {
        method: "GET",
        headers: { Authorization: `Token ${token}` },
      });

      const data = await response.json();

      if (response.ok) {
        setUser(data.user);
        setProfile(data.profile);
        setResumes(data.resumes);
        setEditForm({
          username: data.user.username,
          email: data.user.email,
          bio: data.profile.bio || "",
          profile_picture: null,
        });

        setCountry(data.profile.country || "");
        setRegion(data.profile.governorate || "");

        console.log("Fetched Country:", data.profile.country);
        console.log("Fetched Governorate:", data.profile.governorate);
      } else {
        setError("Failed to fetch profile data.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  // ✅ Call fetchUserProfile inside useEffect to load data initially
  useEffect(() => {
    fetchUserProfile();
  }, []);

  // ✅ Call fetchUserProfile inside handleUpdateProfile to refresh data
  const handleUpdateProfile = async () => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");

    const formData = new FormData();
    formData.append("username", editForm.username);
    formData.append("email", editForm.email);
    formData.append("bio", editForm.bio);
    formData.append("country", country ? country.toString() : "");
    formData.append("governorate", region ? region.toString() : "");

    if (editForm.profile_picture) {
      formData.append("profile_picture", editForm.profile_picture);
    }

    try {
      const response = await fetch(
        "http://localhost:8000/api/profile/update/",
        {
          method: "PUT",
          headers: {
            Authorization: `Token ${token}`,
          },
          body: formData,
        }
      );

      const updatedData = await response.json();

      if (response.ok) {
        setUser(updatedData.user);
        setProfile(updatedData.profile);

        setEditForm({
          username: updatedData.user.username,
          email: updatedData.user.email,
          bio: updatedData.profile.bio,
          profile_picture: null,
        });

        setCountry(updatedData.profile.country);
        setRegion(updatedData.profile.governorate);

        // ✅ Refresh profile picture after updating
        fetchUserProfile();

        alert("Profile updated successfully!");
        setEditModal(false);
      } else {
        setError("Failed to update profile.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  // ✅ Handle Logout
  const handleLogout = async () => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");

    try {
      const response = await fetch("http://localhost:8000/api/logout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
      });

      if (response.ok) {
        sessionStorage.removeItem("authToken");
        localStorage.removeItem("authToken");
        navigate("/login-page");
      } else {
        setError("Failed to log out.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  return (
    <>
      <DemoNavbar />
      <section className="section-profile-cover section-shaped my-0">
        <div className="shape shape-style-1 shape-default alpha-4">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
        <div className="separator separator-bottom separator-skew">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            preserveAspectRatio="none"
            viewBox="0 0 2560 100"
          >
            <polygon className="fill-white" points="2560 0 2560 100 0 100" />
          </svg>
        </div>
      </section>
      <Container>
        <Card className="card-profile shadow mt--300">
          <div className="px-4 py-5 mt-n5 position-relative">
            <div className="position-absolute top-0 end-0 p-3">
              <Button
                color="primary"
                size="sm"
                onClick={() => setEditModal(true)}
                className="me-2"
              >
                <FaEdit /> Edit
              </Button>
              {user && (
                <Button color="danger" size="sm" onClick={handleLogout}>
                  <FaSignOutAlt /> Logout
                </Button>
              )}
            </div>

            <Row className="justify-content-center">
              <Col lg="3" className="text-center">
                <div
                  className="card-profile-image mb-2"
                  style={{ marginTop: "-55px" }}
                >
                  <img
                    alt="Profile"
                    className="rounded-circle"
                    width="150px"
                    height="150px"
                    src={
                      profile?.profile_picture ||
                      require("assets/img/theme/image.png")
                    }
                  />
                </div>
              </Col>
            </Row>

            <div className="text-center mt-4">
              {error && <div className="alert alert-danger">{error}</div>}

              {user ? (
                <>
                  <h2>{user.username}</h2>
                  <p className="text-muted">{user.email}</p>
                  <p>
                    {profile.country || "Country not set"}
                    {profile.governorate ? ", " + profile.governorate : ""}
                  </p>
                  <p>{profile.bio || "No bio available"}</p>
                  <hr className="my-4" />
                  <h4 className="font-weight-bold">Uploaded Resumes</h4>
                  {resumes.length > 0 ? (
                    <ListGroup className="mt-3">
                      {resumes.map((resume) => (
                        <ListGroupItem
                          key={resume.id}
                          className="d-flex justify-content-between align-items-center"
                        >
                          <a
                            href={resume.file}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary"
                          >
                            {resume.title}
                          </a>
                          <Button size="sm" color="danger">
                            Delete
                          </Button>
                        </ListGroupItem>
                      ))}
                    </ListGroup>
                  ) : (
                    <p className="text-muted mt-3">No resumes uploaded.</p>
                  )}
                </>
              ) : (
                <div className="spinner-border text-primary" role="status">
                  <span className="sr-only">Loading...</span>
                </div>
              )}
            </div>
          </div>
        </Card>
      </Container>

      <SimpleFooter />

      {/* Edit Profile Modal */}
      <Modal isOpen={editModal} toggle={() => setEditModal(!editModal)}>
        <ModalHeader toggle={() => setEditModal(!editModal)}>
          Edit Profile
        </ModalHeader>
        <ModalBody>
          <Form>
            <FormGroup>
              <label>Country</label>
              <CountryDropdown
                value={country}
                onChange={(val) => setCountry(val)}
                className="form-control"
              />
            </FormGroup>
            <FormGroup>
              <label className="mt-3">Governorate</label>
              <RegionDropdown
                country={country}
                value={region}
                onChange={(val) => setRegion(val)}
                className="form-control"
              />
            </FormGroup>
            <FormGroup>
              <Input
                type="textarea"
                name="bio"
                placeholder="Bio"
                value={editForm.bio}
                onChange={(e) =>
                  setEditForm({ ...editForm, bio: e.target.value })
                }
              />
            </FormGroup>
            <FormGroup>
              <Input
                type="file"
                name="profile_picture"
                accept="image/*"
                onChange={(e) => {
                  const file = e.target.files[0];
                  if (file && file.type.startsWith("image/")) {
                    setEditForm({ ...editForm, profile_picture: file });
                  } else {
                    alert("Only image files are allowed.");
                    e.target.value = "";
                  }
                }}
              />
            </FormGroup>
          </Form>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" onClick={() => setEditModal(!editModal)}>
            Cancel
          </Button>
          <Button color="primary" onClick={handleUpdateProfile}>
            Save Changes
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
};

export default Profile;
