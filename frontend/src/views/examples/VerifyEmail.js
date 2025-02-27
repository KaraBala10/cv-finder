import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Container,
  Row,
  Col,
  Card,
  CardBody,
  Form,
  FormGroup,
  Input,
  Button,
} from "reactstrap";
import DemoNavbar from "components/Navbars/DemoNavbar.js";
import SimpleFooter from "components/Footers/SimpleFooter.js";

const useQuery = () => {
  return new URLSearchParams(useLocation().search);
};

const VerifyEmail = () => {
  const query = useQuery();
  const email = query.get("email") || "";
  const username = query.get("username") || "";
  const navigate = useNavigate();

  const [verificationCode, setVerificationCode] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_HOST}/verify-email/`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            username,
            verification_code: verificationCode,
          }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setSuccessMessage(data.message);
        setTimeout(() => {
          navigate("/login-page");
        }, 1500);
      } else {
        setErrorMessage(data.error || "Verification failed.");
      }
    } catch (error) {
      setErrorMessage("Network error. Please try again.");
    }
  };

  return (
    <>
      <DemoNavbar />
      <main>
        <section className="section section-shaped section-lg">
          <Container className="pt-lg-7">
            <Row className="justify-content-center">
              <Col lg="5">
                <Card className="bg-secondary shadow border-0">
                  <CardBody className="px-lg-5 py-lg-5">
                    <h3 className="text-center mb-4">Verify Email</h3>
                    {errorMessage && (
                      <div className="alert alert-danger">{errorMessage}</div>
                    )}
                    {successMessage && (
                      <div className="alert alert-success">
                        {successMessage}
                      </div>
                    )}
                    <Form onSubmit={handleSubmit}>
                      <FormGroup>
                        <Input
                          placeholder="Enter verification code"
                          type="text"
                          value={verificationCode}
                          onChange={(e) => setVerificationCode(e.target.value)}
                          required
                        />
                      </FormGroup>
                      <Button
                        type="submit"
                        color="primary"
                        className="mt-4"
                        block
                      >
                        Verify Email
                      </Button>
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

export default VerifyEmail;
