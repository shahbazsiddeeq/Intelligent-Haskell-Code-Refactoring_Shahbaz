import React from "react";
import PropTypes from "prop-types";
import { Row, Col, Card, CardHeader, CardBody, Button } from "shards-react";

import RangeDatePicker from "../common/RangeDatePicker";
import Chart from "../../utils/chart";

class CyclomaticComplexityOverview extends React.Component {
  constructor(props) {
    super(props);
    this.canvasRef = React.createRef();
    this.state = {
      chartData: {
        labels: [],
        datasets: []
      }
    };
  }

  componentDidMount() {
    fetch("http://localhost:8000/result_json")
      .then((res) => res.json())
      .then((data) => {
        const preData = data.analysis.pre_refactor.files || {};
        const postData = data.analysis.post_refactor.hybrid.one_shot.files || {};

        // const allFiles = Array.from(new Set([
        //   ...Object.keys(preData),
        //   ...Object.keys(postData)
        // ]));
        console.log(preData);
        // console.log(postData);
        // const labels = allFiles;

        const matchedFiles = preData
        .filter(preFile => {
            return postData.some(postFile => postFile.file_name.includes(preFile.file_name.split('/pre_refactor/')[1]));
        })
        .map(preFile => {
            const relativePath = preFile.file_name.split('/pre_refactor/')[1];
            const matchingPost = postData.find(postFile =>
            postFile.file_name.includes(relativePath)
            );

            return {
            file_name: preFile.file_name,
            pre_cc: String(preFile.cyclomatic_complexity.sum || "0"),
            post_cc: String(matchingPost.cyclomatic_complexity.sum || "0")
            };
        });

        console.log(matchedFiles);

        const labels = matchedFiles.map(file => {
            // console.log("pre:" + preData[file].file_name);
            // console.log("post:" + postData[file].file_name);
            return file.file_name.split('/pre_refactor/').pop() || "unknown";

        });

        const preValues = matchedFiles.map(file => {
            // console.log("pre:" + preData[file].file_name);
            // console.log("post:" + postData[file].file_name);
            return file.pre_cc || 0;

        });
        const postValues = matchedFiles.map(file => {
            // console.log("pre:" + preData[file].file_name);
            // console.log("post:" + postData[file].file_name);
            return file.post_cc || 0;

        });
        

        // const preValues = [];
        // const postValues = [];
        // const postValues = allFiles.map(file => {
        //     const postCCValue =
        //         postData[file] &&
        //         postData[file].cyclomatic_complexity &&
        //         postData[file].cyclomatic_complexity.sum
        //         ? postData[file].cyclomatic_complexity.sum
        //         : preData[file].cyclomatic_complexity.sum;
            
        //         return postCCValue;
        //     // return postData[file].cyclomatic_complexity.sum || preData[file].cyclomatic_complexity.sum || 0;
        // });
        // console.log("pre:"+preValues+ " post" + postValues)


        

        

        const chartData = {
          labels: labels,
          datasets: [
            {
              label: "Pre Refactor",
              data: preValues,
              fill: false,
              backgroundColor: "rgba(0,123,255,0.1)",
              borderColor: "rgba(0,123,255,1)",
              borderWidth: 1.5
            },
            {
              label: "Post Refactor",
              data: postValues,
              fill: false,
              backgroundColor: "rgba(40,200,80,0.1)",
              borderColor: "rgba(40,200,80,1)",
              borderDash: [5, 5],
              borderWidth: 1.5
            }
          ]
        };

        this.setState({ chartData }, () => {
          this.renderChart();
        });
      })
      .catch(err => {
        console.error("Failed to fetch complexity data:", err);
      });
  }

  renderChart() {
    const chartOptions = {
      responsive: true,
      legend: {
        position: "top"
      },
      elements: {
        line: {
          tension: 0.3
        },
        point: {
          radius: 0
        }
      },
      scales: {
        xAxes: [
          {
            ticks: {
              autoSkip: false,
              maxRotation: 90,
              minRotation: 45
            }
          }
        ],
        yAxes: [
          {
            ticks: {
              suggestedMax: 20,
              beginAtZero: true
            }
          }
        ]
      },
      hover: {
        mode: "nearest",
        intersect: false
      },
      tooltips: {
        mode: "nearest",
        intersect: false
      }
    };

    new Chart(this.canvasRef.current, {
      type: "line",
      data: this.state.chartData,
      options: chartOptions
    });
  }

  render() {
    const { title } = this.props;
    return (
      <Card small className="h-100">
        <CardHeader className="border-bottom">
          <h6 className="m-0">{title}</h6>
        </CardHeader>
        <CardBody className="pt-0">
          <Row className="border-bottom py-2 bg-light">
            <Col sm="6" className="d-flex mb-2 mb-sm-0">
              <RangeDatePicker />
            </Col>
            <Col>
              <Button
                size="sm"
                className="d-flex btn-white ml-auto mr-auto ml-sm-auto mr-sm-0 mt-3 mt-sm-0"
              >
                View Full Report &rarr;
              </Button>
            </Col>
          </Row>
          <canvas height="120" ref={this.canvasRef} style={{ maxWidth: "100%" }} />
        </CardBody>
      </Card>
    );
  }
}

CyclomaticComplexityOverview.propTypes = {
  title: PropTypes.string
};

CyclomaticComplexityOverview.defaultProps = {
  title: "Cyclomatic Complexity per File"
};

export default CyclomaticComplexityOverview;
