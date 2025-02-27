import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
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
  const { username: routeUsername } = useParams();
  const [currentUser, setCurrentUser] = useState(null);
  const [profileUser, setProfileUser] = useState(null);
  const [profile, setProfile] = useState({});
  const [resumes, setResumes] = useState([]);
  const [error, setError] = useState("");
  const [editModal, setEditModal] = useState(false);
  const [resumeModal, setResumeModal] = useState(false);
  const [viewModal, setViewModal] = useState(false);
  const [selectedResume, setSelectedResume] = useState(null);
  const [invalidTokenDialog, setInvalidTokenDialog] = useState(false);
  const [editForm, setEditForm] = useState({
    username: "",
    email: "",
    bio: "",
    profile_picture: null,
  });
  const [country, setCountry] = useState("");
  const [region, setRegion] = useState("");

  const [resumeFile, setResumeFile] = useState(null);
  const [resumeError, setResumeError] = useState("");
  const [resumeSuccess, setResumeSuccess] = useState("");
  const isOwnProfile =
    !routeUsername || (currentUser && routeUsername === currentUser.username);

  const fetchCurrentUser = async () => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");
    if (!token) {
      if (!routeUsername) {
        navigate("/login-page");
      }
      return;
    }
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_HOST}/profile/`,
        {
          method: "GET",
          headers: { Authorization: `Token ${token}` },
        }
      );
      const data = await response.json();
      if (response.ok) {
        setCurrentUser(data.user);
        if (!routeUsername) {
          setProfileUser(data.user);
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
        }
      } else {
        setError("Failed to fetch current user profile.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };
  const handleLogout = async () => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");
    try {
      await fetch(`${process.env.REACT_APP_API_HOST}/logout/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${token}`,
        },
      });
    } catch (error) {
    } finally {
      sessionStorage.removeItem("authToken");
      localStorage.removeItem("authToken");
      navigate("/login-page");
    }
  };
  const fetchPublicProfile = async () => {
    const url = `${process.env.REACT_APP_API_HOST}/profile/${routeUsername}/`;
    try {
      const response = await fetch(url, { method: "GET" });
      const data = await response.json();
      if (response.ok) {
        setProfileUser(data.user);
        setProfile(data.profile);
        setResumes(data.resumes);
      } else {
        setError("Failed to fetch public profile data.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  useEffect(() => {
    fetchCurrentUser();
    if (routeUsername) {
      fetchPublicProfile();
    }
  }, [routeUsername]);

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
        `${process.env.REACT_APP_API_HOST}/profile/update/`,
        {
          method: "PUT",
          headers: { Authorization: `Token ${token}` },
          body: formData,
        }
      );
      const updatedData = await response.json();
      if (response.ok) {
        setCurrentUser(updatedData.user);
        setProfileUser(updatedData.user);
        setProfile(updatedData.profile);
        setEditForm({
          username: updatedData.user.username,
          email: updatedData.user.email,
          bio: updatedData.profile.bio,
          profile_picture: null,
        });
        setCountry(updatedData.profile.country);
        setRegion(updatedData.profile.governorate);
        fetchCurrentUser();
        alert("Profile updated successfully!");
        setEditModal(false);
      } else {
        setError("Failed to update profile.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  const handleCloseInvalidTokenDialog = () => {
    setInvalidTokenDialog(false);
    handleLogout();
  };

  const handleResumeUpload = async (e) => {
    e.preventDefault();
    setResumeError("");
    setResumeSuccess("");
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");
    if (!resumeFile) {
      setResumeError("Resume file is required.");
      return;
    }
    const formData = new FormData();
    formData.append("title", `${currentUser.username}_resume`);
    formData.append("file", resumeFile);
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_HOST}/resume/upload/`,
        {
          method: "POST",
          headers: { Authorization: `Token ${token}` },
          body: formData,
        }
      );
      const data = await response.json();
      if (response.ok) {
        fetchCurrentUser();
        setResumeFile(null);
        setResumeModal(false);
      } else {
        setResumeError(data.error || "Error uploading resume.");
      }
    } catch (error) {
      setResumeError("Network error. Please try again.");
    }
  };

  const handleDeleteResume = async (resumeId) => {
    const token =
      sessionStorage.getItem("authToken") || localStorage.getItem("authToken");
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_HOST}/resume/delete/${resumeId}/`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${token}`,
          },
        }
      );
      if (response.status === 204) {
        if (isOwnProfile) {
          fetchCurrentUser();
        } else {
          fetchPublicProfile();
        }
      } else {
        const data = await response.json();
        setResumeError(data.error || "Error deleting resume.");
      }
    } catch (error) {
      setResumeError("Network error. Please try again.");
    }
  };

  const handleViewResume = (resume) => {
    const viewUrl = `${process.env.REACT_APP_API_HOST}/resume/view/${profileUser.username}/`;
    setSelectedResume({ ...resume, viewUrl });
    setViewModal(true);
  };

  const handleDownloadResume = async () => {
    try {
      const url = `${process.env.REACT_APP_API_HOST}/resume/download/${profileUser.username}/`;
      const response = await fetch(url, { method: "GET" });
      if (!response.ok) {
        throw new Error("Download failed");
      }
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = `${profileUser.username}_resume.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Error downloading resume:", error);
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
          <div className="position-relative">
            <div className="d-flex justify-content-end p-3">
              {isOwnProfile && (
                <>
                  <Button
                    color="primary"
                    size="sm"
                    onClick={() => setEditModal(true)}
                    className="me-2"
                  >
                    <FaEdit /> Edit
                  </Button>
                  <Button color="danger" size="sm" onClick={handleLogout}>
                    <FaSignOutAlt /> Logout
                  </Button>
                </>
              )}
            </div>
            <Row className="justify-content-center">
              <Col lg="3" className="text-center">
                <div
                  className="card-profile-image mb-2"
                  style={{
                    marginTop: "-110px",
                    maxWidth: "150px",
                    marginLeft: "auto",
                    marginRight: "auto",
                  }}
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
              {profileUser ? (
                <>
                  <h2>{profileUser.username}</h2>
                  <p className="text-muted">{profileUser.email}</p>
                  <p>
                    {profile.country || "Country not set"}
                    {profile.governorate ? ", " + profile.governorate : ""}
                  </p>
                  <p>{profile.bio || "No bio available"}</p>
                  <hr className="my-4" />
                  {resumes.length > 0 ? (
                    <>
                      <h4 className="font-weight-bold mb-4">Resume</h4>
                      <ListGroup className="mt-3">
                        {resumes.map((resume) => (
                          <ListGroupItem
                            key={resume.id}
                            className="d-flex justify-content-between align-items-center p-3 mb-2 shadow-sm"
                          >
                            <div>
                              <Button
                                color="link"
                                onClick={() => handleViewResume(resume)}
                                style={{
                                  textDecoration: "underline",
                                  fontSize: "1.1rem",
                                }}
                              >
                                {resume.title}
                              </Button>
                            </div>
                            <div>
                              <Button
                                size="sm"
                                color="primary"
                                onClick={handleDownloadResume}
                              >
                                Download
                              </Button>
                              {isOwnProfile && (
                                <Button
                                  size="sm"
                                  color="danger"
                                  className="mr-2"
                                  onClick={() => handleDeleteResume(resume.id)}
                                >
                                  Delete
                                </Button>
                              )}
                            </div>
                          </ListGroupItem>
                        ))}
                      </ListGroup>
                    </>
                  ) : (
                    isOwnProfile && (
                      <div className="mt-4">
                        <Button
                          color="primary"
                          style={{ marginBottom: "25px" }}
                          onClick={() => setResumeModal(true)}
                        >
                          Upload Resume
                        </Button>
                      </div>
                    )
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

      <Modal isOpen={resumeModal} toggle={() => setResumeModal(!resumeModal)}>
        <ModalHeader toggle={() => setResumeModal(!resumeModal)}>
          Upload Resume
        </ModalHeader>
        <ModalBody>
          {resumeError && (
            <div className="alert alert-danger">{resumeError}</div>
          )}
          {resumeSuccess && (
            <div className="alert alert-success">{resumeSuccess}</div>
          )}
          <Form onSubmit={handleResumeUpload}>
            <FormGroup>
              <Input
                type="file"
                name="resumeFile"
                accept=".pdf"
                onChange={(e) => setResumeFile(e.target.files[0] || null)}
                required
              />
            </FormGroup>
          </Form>
        </ModalBody>
        <ModalFooter>
          <Button color="secondary" onClick={() => setResumeModal(false)}>
            Cancel
          </Button>
          <Button color="primary" onClick={handleResumeUpload}>
            Upload Resume
          </Button>
        </ModalFooter>
      </Modal>

      <Modal
        isOpen={viewModal}
        toggle={() => setViewModal(!viewModal)}
        size="lg"
      >
        <ModalHeader toggle={() => setViewModal(!viewModal)}>
          View Resume
        </ModalHeader>
        <ModalBody>
          {selectedResume && selectedResume.viewUrl ? (
            <iframe
              src={selectedResume.viewUrl}
              title={selectedResume.title}
              width="100%"
              height="600px"
            ></iframe>
          ) : (
            <p>No resume selected.</p>
          )}
        </ModalBody>
        <ModalFooter>
          <Button color="primary" onClick={handleDownloadResume}>
            Download Resume
          </Button>
          <Button color="secondary" onClick={() => setViewModal(false)}>
            Close
          </Button>
        </ModalFooter>
      </Modal>

      <Modal isOpen={invalidTokenDialog}>
        <ModalHeader>Session Expired</ModalHeader>
        <ModalBody>
          Your session has expired or is invalid. Please log in again.
        </ModalBody>
        <ModalFooter>
          <Button color="primary" onClick={handleCloseInvalidTokenDialog}>
            OK
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
};

export default Profile;
