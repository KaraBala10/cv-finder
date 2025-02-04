import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
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
import { FaEdit } from "react-icons/fa"; // ✅ Import edit icon
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
    location: "",
  });

  useEffect(() => {
    const fetchUserProfile = async () => {
      const token = localStorage.getItem("authToken");

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
            location: data.profile.location || "",
          });
        } else {
          setError("Failed to fetch profile data.");
        }
      } catch (error) {
        setError("Network error. Please try again.");
      }
    };

    fetchUserProfile();
  }, [navigate]);

  // Toggle Edit Modal
  const toggleEditModal = () => {
    setEditModal(!editModal);
  };

  // Handle Input Change
  const handleInputChange = (event) => {
    setEditForm({ ...editForm, [event.target.name]: event.target.value });
  };

  // Submit Updated Profile
  const handleUpdateProfile = async () => {
    const token = localStorage.getItem("authToken");

    try {
      const response = await fetch(
        "http://localhost:8000/api/profile/update/",
        {
          method: "PUT", // ✅ Change to PUT
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${token}`,
          },
          body: JSON.stringify({
            username: editForm.username,
            email: editForm.email,
            bio: editForm.bio,
            location: editForm.location,
          }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        alert("Profile updated successfully!");
        setUser({
          ...user,
          username: editForm.username,
          email: editForm.email,
        });
        setProfile({
          ...profile,
          bio: editForm.bio,
          location: editForm.location,
        });
        toggleEditModal();
      } else {
        setError("Failed to update profile.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  return (
    <>
      <DemoNavbar />
      <main className="profile-page">
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

        <section className="section">
          <Container>
            <Card className="card-profile shadow mt--300">
              <div className="px-4 py-5 mt-n5 position-relative">
                {/* Edit Button at Top-Right Corner */}
                <div className="position-absolute top-0 end-0 p-3">
                  <Button color="primary" size="sm" onClick={toggleEditModal}>
                    <FaEdit /> Edit
                  </Button>
                </div>

                <Row className="justify-content-center">
                  <Col lg="3" className="text-center">
                    <div className="card-profile-image mb-7">
                      <img
                        alt="Profile"
                        className="rounded-circle"
                        width="150px"
                        height="150px"
                        src={require("assets/img/theme/team-4-800x800.jpg")}
                      />
                    </div>
                  </Col>
                </Row>

                <div className="text-center mt-4">
                  {error && <div className="alert alert-danger">{error}</div>}

                  {user ? (
                    <>
                      <h2 className="font-weight-bold">{user.username}</h2>
                      <p className="text-muted">{user.email}</p>
                      <p>
                        <i className="ni location_pin mr-2"></i>{" "}
                        {profile.location || "Location not set"}
                      </p>
                      <p className="text-muted">
                        {profile.bio || "No bio available"}
                      </p>

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
        </section>
      </main>
      <SimpleFooter />

      {/* Edit Profile Modal */}
      <Modal isOpen={editModal} toggle={toggleEditModal}>
        <ModalHeader toggle={toggleEditModal}>Edit Profile</ModalHeader>
        <ModalBody>
          <Form>
            <FormGroup>
              <Input
                type="text"
                name="username"
                placeholder="Username"
                value={editForm.username}
                onChange={handleInputChange}
              />
            </FormGroup>
            <FormGroup>
              <Input
                type="email"
                name="email"
                placeholder="Email"
                value={editForm.email}
                onChange={handleInputChange}
              />
            </FormGroup>
            <FormGroup>
              <Input
                type="text"
                name="location"
                placeholder="Location"
                value={editForm.location}
                onChange={handleInputChange}
              />
            </FormGroup>
            <FormGroup>
              <Input
                type="textarea"
                name="bio"
                placeholder="Bio"
                value={editForm.bio}
                onChange={handleInputChange}
              />
            </FormGroup>
          </Form>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" onClick={toggleEditModal}>
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
