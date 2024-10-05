import logging
import os
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

logging.basicConfig(level=logging.INFO)


class ExtractTextTableInfoWithFiguresTablesRenditionsFromPDF:
    """
    Class to extract text, tables, figures, and renditions from a PDF file using Adobe PDF Services.
    """

    def __init__(self, file):
        """
        Initialize the extractor with the given PDF file.

        :param file: A file-like object representing the PDF to be processed.
        """
        self.result = None
        self.stream_asset: StreamAsset = None
        try:
            input_stream = file.read()
            file.seek(0)

            credentials = ServicePrincipalCredentials(
                client_id=str(os.getenv('PDF_SERVICES_CLIENT_ID')),
                client_secret=str(os.getenv('PDF_SERVICES_CLIENT_SECRET'))
            )
            pdf_services = PDFServices(credentials=credentials)
            input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)

            extract_pdf_params = ExtractPDFParams(
                elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
                elements_to_extract_renditions=[ExtractRenditionsElementType.TABLES, ExtractRenditionsElementType.FIGURES],
            )

            extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)
            location = pdf_services.submit(extract_pdf_job)
            pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)

            result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
            self.stream_asset = pdf_services.get_content(result_asset)
        except (ServiceApiException, ServiceUsageException, SdkException) as e:
            logging.exception('Exception encountered while executing operation: %s', e)
            raise

    def get_result(self):
        """
        Retrieve the extracted content from the PDF.

        :return: Input stream of the extracted content or None if extraction failed.
        """
        if self.stream_asset:
            return self.stream_asset.get_input_stream()
        else:
            return None
