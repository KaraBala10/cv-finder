import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Button,
  Card,
  CardHeader,
  CardBody,
  FormGroup,
  Form,
  Input,
  InputGroupAddon,
  InputGroupText,
  InputGroup,
  Container,
  Row,
  Col,
} from "reactstrap";
import DemoNavbar from "components/Navbars/DemoNavbar.js";
import SimpleFooter from "components/Footers/SimpleFooter.js";

const ResetPassword = () => {
  const { uid, token } = useParams(); // Capture uid and token from the URL
  const navigate = useNavigate();
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Optionally, validate the token or load data from API here
  }, [uid, token]);

  const handleChange = (e) => {
    if (e.target.name === "newPassword") {
      setNewPassword(e.target.value);
    } else if (e.target.name === "confirmPassword") {
      setConfirmPassword(e.target.value);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(""); // Reset error state
    setMessage(""); // Reset message state

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/api/password-reset/confirm/${uid}/${token}/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: newPassword }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setMessage("Password reset successfully. You can now log in.");
        setTimeout(() => navigate("/login"), 3000); // Redirect to login page after success
      } else {
        setError(data.error || "Error resetting password.");
      }
    } catch (error) {
      setError("Network error. Please try again.");
    }
  };

  return (
    <>
      <DemoNavbar />
      <main>
        <section className="section section-shaped section-lg">
          <div className="shape shape-style-1 bg-gradient-default">
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
            <span />
          </div>
          <Container className="pt-lg-7">
            <Row className="justify-content-center">
              <Col lg="5">
                <Card className="bg-secondary shadow border-0">
                  <CardHeader className="bg-white pb-5">
                    <div className="text-muted text-center mb-3">
                      <small>Reset your password</small>
                    </div>
                  </CardHeader>
                  <CardBody className="px-lg-5 py-lg-5">
                    <div className="text-center text-muted mb-4">
                      <small>Enter a new password</small>
                    </div>
                    {error && <div className="alert alert-danger">{error}</div>}
                    {message && (
                      <div className="alert alert-success">{message}</div>
                    )}
                    <Form onSubmit={handleSubmit}>
                      <FormGroup className="mb-3">
                        <InputGroup className="input-group-alternative">
                          <InputGroupAddon addonType="prepend">
                            <InputGroupText>
                              <i className="ni ni-lock-circle-open" />
                            </InputGroupText>
                          </InputGroupAddon>
                          <Input
                            name="newPassword"
                            type="password"
                            placeholder="New Password"
                            value={newPassword}
                            onChange={handleChange}
                            required
                          />
                        </InputGroup>
                      </FormGroup>
                      <FormGroup className="mb-3">
                        <InputGroup className="input-group-alternative">
                          <InputGroupAddon addonType="prepend">
                            <InputGroupText>
                              <i className="ni ni-lock-circle-open" />
                            </InputGroupText>
                          </InputGroupAddon>
                          <Input
                            name="confirmPassword"
                            type="password"
                            placeholder="Confirm Password"
                            value={confirmPassword}
                            onChange={handleChange}
                            required
                          />
                        </InputGroup>
                      </FormGroup>
                      <div className="text-center">
                        <Button className="my-4" color="primary" type="submit">
                          Reset Password
                        </Button>
                      </div>
                    </Form>
                  </CardBody>
                </Card>
              </Col>
            </Row>
          </Container>
        </section>
      </main>
      <SimpleFooter />
    </>
  );
};

export default ResetPassword;
