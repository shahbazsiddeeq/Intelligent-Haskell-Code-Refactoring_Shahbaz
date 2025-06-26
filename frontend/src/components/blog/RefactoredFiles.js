import React from "react";
import PropTypes from "prop-types";
import {
  Row,
  Col,
  Card,
  CardHeader,
  CardBody,
  CardFooter
} from "shards-react";

import Chart from "../../utils/chart";

class RefactoredFiles extends React.Component {
  constructor(props) {
    super(props);
    this.canvasRef = React.createRef();
    this.state = {
      chartData: {
        datasets: [
          {
            hoverBorderColor: "#ffffff",
            data: [0, 0],
            backgroundColor: [
              "rgba(0,123,255,0.9)",
              "rgba(0,123,255,0.5)"
            ]
          }
        ],
        labels: ["Refactored", "Non-Refactored"]
      }
    };
  }

  componentDidMount() {
    fetch("http://localhost:8000/result_json")
      .then((res) => res.json())
      .then((data) => {
        const preFiles = data.analysis.pre_refactor.files || [];
        const postFiles = data.analysis.post_refactor.hybrid.one_shot.files || [];

        const preFileNames = preFiles.map(f => f.file_name.split("/pre_refactor/").pop());
        const postFileNames = postFiles.map(f => f.file_name.split("/pre_refactor/").pop());

        let refactoredCount = 0;
        let nonRefactoredCount = 0;

        preFileNames.forEach(file => {
          if (postFileNames.includes(file)) {
            refactoredCount++;
          } else {
            nonRefactoredCount++;
          }
        });

        this.setState(
          {
            chartData: {
              labels: ["Refactored", "Non-Refactored"],
              datasets: [
                {
                  hoverBorderColor: "#ffffff",
                  data: [refactoredCount, nonRefactoredCount],
                  backgroundColor: [
                    "rgba(0,123,255,0.9)",
                    "rgba(0,123,255,0.5)"
                  ]
                }
              ]
            }
          },
          () => this.renderChart()
        );
      })
      .catch((err) => {
        console.error("Failed to fetch file data:", err);
      });
  }

  renderChart() {
    const chartConfig = {
      type: "pie",
      data: this.state.chartData,
      options: {
        legend: {
          position: "bottom",
          labels: {
            padding: 25,
            boxWidth: 20
          }
        },
        cutoutPercentage: 0,
        tooltips: {
          custom: false,
          mode: "index",
          position: "nearest"
        }
      }
    };

    new Chart(this.canvasRef.current, chartConfig);
  }

  render() {
    const { title } = this.props;

    return (
      <Card small className="h-100">
        <CardHeader className="border-bottom">
          <h6 className="m-0">{title}</h6>
        </CardHeader>
        <CardBody className="d-flex py-0">
          <canvas
            height="220"
            ref={this.canvasRef}
            className="blog-users-by-device m-auto"
          />
        </CardBody>
        <CardFooter className="border-top">
          <Row>
            <Col className="text-center">
              Showing refactored vs non-refactored files.
            </Col>
          </Row>
        </CardFooter>
      </Card>
    );
  }
}

RefactoredFiles.propTypes = {
  title: PropTypes.string
};

RefactoredFiles.defaultProps = {
  title: "Refactored Files"
};

export default RefactoredFiles;
