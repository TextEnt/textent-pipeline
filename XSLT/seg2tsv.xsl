<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    exclude-result-prefixes="xs"
    xpath-default-namespace="http://www.tei-c.org/ns/1.0"
    version="2.0">
    
    <xsl:output method="text" encoding="UTF-8"/>
    
    <xsl:template match="@*|node()">
        <xsl:apply-templates select="@*|node()"/>
    </xsl:template>
    
    <xsl:template match="seg">
        <xsl:value-of select="./orig"/><xsl:text>&#09;</xsl:text><xsl:value-of select="./reg"/><xsl:text>&#xA;</xsl:text>
    </xsl:template>
    
</xsl:stylesheet>